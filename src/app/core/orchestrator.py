from __future__ import annotations

from pathlib import Path

import yaml

from app.agents.reviewer import ReviewerAgent
from app.agents.summarizer import SummarizerAgent
from app.agents.worldbuilder import WorldBuilderAgent
from app.agents.writer import WriterAgent
from app.core.llm_client import LLMClient
from app.core.prompt_loader import load_prompt
from app.domain.models import AgentConfig, AgentDefaults, BookMeta, ReviewResult
from app.domain.policies import ReviewPolicy
from app.services.chapter_context import ChapterContextService
from app.services.review_pipeline import ReviewPipeline
from app.storage.fs_repo import FileRepository
from app.storage.snapshots import SnapshotStore


class Orchestrator:
    REVIEWER_NAMES = ["reviewer_style", "reviewer_plot", "reviewer_character"]

    def __init__(self, root: Path) -> None:
        self.root = root
        self.repo = FileRepository(root)
        self.snapshots = SnapshotStore(self.repo)
        self.llm = LLMClient()

    def _load_agent_defaults(self) -> AgentDefaults:
        path = self.root / "agents" / "defaults.yaml"
        if not path.exists():
            return AgentDefaults()
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return AgentDefaults(**data)

    def _load_agent_config(self, name: str) -> AgentConfig:
        defaults = self._load_agent_defaults()
        path = self.root / "agents" / f"{name}.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        cfg = AgentConfig(**data)

        resolved_model = cfg.model or defaults.model
        if not resolved_model:
            raise ValueError(f"Agent '{name}' missing model and no defaults.model configured")

        return AgentConfig(
            name=cfg.name,
            model=resolved_model,
            temperature=cfg.temperature if cfg.temperature is not None else defaults.temperature,
            max_output_tokens=cfg.max_output_tokens if cfg.max_output_tokens is not None else defaults.max_output_tokens,
            system_prompt_file=cfg.system_prompt_file,
        )

    def _build_writer(self) -> WriterAgent:
        cfg = self._load_agent_config("writer")
        system_prompt = load_prompt(self.root / cfg.system_prompt_file)
        return WriterAgent(cfg, self.llm, system_prompt)

    def _build_summarizer(self) -> SummarizerAgent:
        cfg = self._load_agent_config("summarizer")
        system_prompt = load_prompt(self.root / cfg.system_prompt_file)
        return SummarizerAgent(cfg, self.llm, system_prompt)

    def _build_worldbuilder(self) -> WorldBuilderAgent:
        cfg = self._load_agent_config("worldbuilder")
        system_prompt = load_prompt(self.root / cfg.system_prompt_file)
        return WorldBuilderAgent(cfg, self.llm, system_prompt)

    def _build_reviewers(self) -> list[ReviewerAgent]:
        out: list[ReviewerAgent] = []
        for name in self.REVIEWER_NAMES:
            cfg = self._load_agent_config(name)
            system_prompt = load_prompt(self.root / cfg.system_prompt_file)
            out.append(ReviewerAgent(cfg, self.llm, system_prompt))
        return out

    def _build_review_prompt(self, reviewer_name: str, content: str) -> str:
        """构建统一的评审提示词：指定评审维度 + 当前章节内容。"""
        return (
            "请评审以下小说章节内容。\n\n"
            f"评审维度:{reviewer_name}\n"
            f"内容:\n{content}"
        )

    def _build_writer_prompt(self, context: str, rewrite_feedback: str) -> str:
        """构建写作提示词：章节上下文 + 上一轮评审反馈。"""
        return (
            "请基于以下上下文撰写本章正文，要求叙事连贯、人物一致、对话自然。\n\n"
            f"{context}\n\n"
            f"上轮评审意见（若有）:\n{rewrite_feedback}"
        )

    @staticmethod
    def _format_rewrite_feedback(results: list[ReviewResult]) -> str:
        """将多位评审结果压缩为下一轮可直接使用的反馈文本。"""
        return "\n".join(
            [f"[{r.reviewer}] must_fix={r.must_fix}; issues={r.issues}; suggestions={r.suggestions}" for r in results]
        )

    def _ensure_chapter_ready(self, slug: str, chapter_no: int, brief: str | None) -> tuple[Path, Path]:
        """确保章节目录结构可用，并返回 (chapter_dir, final_md_path)。"""
        chapter_dir = self.repo.chapter_dir(slug, chapter_no)
        if chapter_dir.exists():
            (chapter_dir / "drafts").mkdir(parents=True, exist_ok=True)
            (chapter_dir / "reviews").mkdir(parents=True, exist_ok=True)
        else:
            self.repo.create_chapter(slug, chapter_no, brief)

        return chapter_dir, chapter_dir / "final.md"

    def _resume_state(
        self,
        slug: str,
        chapter_no: int,
        review_pipeline: ReviewPipeline,
    ) -> tuple[int, str]:
        """从已有草稿恢复状态，返回 (下一稿编号, 重写反馈)。"""
        latest_draft_no = self.snapshots.latest_draft_no(slug, chapter_no)
        if latest_draft_no is None:
            return 1, ""

        last_draft_text = self.snapshots.read_draft(slug, chapter_no, latest_draft_no)
        resume_results, _ = review_pipeline.run(
            lambda reviewer_name: self._build_review_prompt(reviewer_name, last_draft_text)
        )
        for rr in resume_results:
            self.snapshots.save_review(slug, chapter_no, latest_draft_no, rr)

        return latest_draft_no + 1, self._format_rewrite_feedback(resume_results)

    def _finalize_chapter(
        self,
        slug: str,
        chapter_no: int,
        chapter_dir: Path,
        draft_text: str,
        summarizer: SummarizerAgent,
    ) -> Path:
        """保存定稿并更新章节摘要与滚动摘要。"""
        final_path = self.snapshots.save_final(slug, chapter_no, draft_text)
        summary_prompt = f"请将以下章节压缩为可用于后续上下文的摘要（300字内）：\n\n{draft_text}"
        summary = summarizer.summarize(summary_prompt)
        (chapter_dir / "summary.md").write_text(summary, encoding="utf-8")

        rolling_path = self.repo.book_dir(slug) / "memory" / "rolling_summary.md"
        old = rolling_path.read_text(encoding="utf-8") if rolling_path.exists() else ""
        rolling_path.write_text(old + f"\n\n## Chapter {chapter_no:03d}\n\n" + summary, encoding="utf-8")
        return final_path

    def create_book(
        self,
        slug: str,
        title: str | None,
        synopsis: str | None,
        characters: str | None,
        worldbuilding: str | None,
    ) -> Path:
        if not all([synopsis, characters, worldbuilding]):
            worldbuilder_agent = self._build_worldbuilder()
            prompt = (
                "请补全一本小说的基础设定，字段包括 synopsis / characters / worldbuilding。\n"
                "仅填写缺失字段，已有字段保持风格统一并与其兼容。\n"
                f"title={title or slug}\n"
                f"synopsis={synopsis or ''}\n"
                f"characters={characters or ''}\n"
                f"worldbuilding={worldbuilding or ''}\n"
            )
            generated = worldbuilder_agent.build_missing(prompt)
            synopsis = synopsis or generated.get("synopsis", "")
            characters = characters or generated.get("characters", "")
            worldbuilding = worldbuilding or generated.get("worldbuilding", "")

        meta = BookMeta(
            slug=slug,
            title=title,
            synopsis=synopsis,
            characters=characters,
            worldbuilding=worldbuilding,
        )
        return self.repo.create_book(meta)

    def write_chapter(self, slug: str, chapter_no: int, brief: str | None = None, max_rounds: int = 20) -> Path:
        """执行“写作-评审”循环（支持断点续跑），直到通过或达到轮次上限。"""
        chapter_dir, final_path = self._ensure_chapter_ready(slug, chapter_no, brief)
        if final_path.exists():
            return final_path

        writer = self._build_writer()
        summarizer = self._build_summarizer()
        review_pipeline = ReviewPipeline(self._build_reviewers(), ReviewPolicy(min_avg_score=80))
        context_service = ChapterContextService(self.repo)

        start_draft_no, rewrite_feedback = self._resume_state(slug, chapter_no, review_pipeline)
        if start_draft_no > max_rounds:
            raise RuntimeError(
                f"Chapter {chapter_no} already has draft_{start_draft_no-1:03d}; increase --max-rounds to continue"
            )

        for draft_no in range(start_draft_no, max_rounds + 1):
            context = context_service.build_context(slug, chapter_no, brief)
            draft_text = writer.write_draft(self._build_writer_prompt(context, rewrite_feedback))
            self.snapshots.save_draft(slug, chapter_no, draft_no, draft_text)

            review_results, ok = review_pipeline.run(
                lambda reviewer_name: self._build_review_prompt(reviewer_name, draft_text)
            )
            for rr in review_results:
                self.snapshots.save_review(slug, chapter_no, draft_no, rr)

            if ok:
                return self._finalize_chapter(slug, chapter_no, chapter_dir, draft_text, summarizer)

            rewrite_feedback = self._format_rewrite_feedback(review_results)

        raise RuntimeError(f"Chapter {chapter_no} failed after {max_rounds} drafts")
