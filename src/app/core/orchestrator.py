from __future__ import annotations

from pathlib import Path

import yaml

from app.agents.reviewer import ReviewerAgent
from app.agents.summarizer import SummarizerAgent
from app.agents.worldbuilder import WorldBuilderAgent
from app.agents.writer import WriterAgent
from app.core.llm_client import LLMClient
from app.core.prompt_loader import load_prompt
from app.domain.models import AgentConfig, AgentDefaults, BookMeta
from app.domain.policies import ReviewPolicy
from app.services.chapter_context import ChapterContextService
from app.services.review_pipeline import ReviewPipeline
from app.storage.fs_repo import FileRepository
from app.storage.snapshots import SnapshotStore


class Orchestrator:
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
        names = ["reviewer_style", "reviewer_plot", "reviewer_character"]
        out: list[ReviewerAgent] = []
        for n in names:
            cfg = self._load_agent_config(n)
            system_prompt = load_prompt(self.root / cfg.system_prompt_file)
            out.append(ReviewerAgent(cfg, self.llm, system_prompt))
        return out

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

    def write_chapter(self, slug: str, chapter_no: int, brief: str | None = None, max_rounds: int = 5) -> Path:
        self.repo.create_chapter(slug, chapter_no, brief)
        writer = self._build_writer()
        reviewers = self._build_reviewers()
        summarizer = self._build_summarizer()
        review_pipeline = ReviewPipeline(reviewers, ReviewPolicy(min_avg_score=80))
        context_service = ChapterContextService(self.repo)

        rewrite_feedback = ""
        for draft_no in range(1, max_rounds + 1):
            context = context_service.build_context(slug, chapter_no, brief)
            writer_prompt = (
                "请基于以下上下文撰写本章草稿，要求叙事连贯、人物一致、对话自然。\n\n"
                f"{context}\n\n"
                f"上轮评审意见（若有）:\n{rewrite_feedback}"
            )
            draft_text = writer.write_draft(writer_prompt)
            self.snapshots.save_draft(slug, chapter_no, draft_no, draft_text)

            def _review_prompt(reviewer_name: str) -> str:
                return (
                    "请严格评审以下小说章节草稿，并仅返回JSON:\n"
                    "{\"reviewer\":\"name\",\"passed\":true/false,\"score\":0-100,\"issues\":[],\"must_fix\":[],\"suggestions\":[]}\n\n"
                    f"评审维度:{reviewer_name}\n"
                    f"草稿:\n{draft_text}"
                )

            review_results, ok = review_pipeline.run(_review_prompt)
            for rr in review_results:
                self.snapshots.save_review(slug, chapter_no, draft_no, rr)

            if ok:
                final_path = self.snapshots.save_final(slug, chapter_no, draft_text)
                chapter_dir = self.repo.chapter_dir(slug, chapter_no)
                summary_prompt = f"请将以下章节压缩为可用于后续上下文的摘要（500字内）：\n\n{draft_text}"
                summary = summarizer.summarize(summary_prompt)
                (chapter_dir / "summary.md").write_text(summary, encoding="utf-8")

                rolling_path = self.repo.book_dir(slug) / "memory" / "rolling_summary.md"
                old = rolling_path.read_text(encoding="utf-8") if rolling_path.exists() else ""
                rolling_path.write_text(old + f"\n\n## Chapter {chapter_no:03d}\n\n" + summary, encoding="utf-8")
                return final_path

            rewrite_feedback = "\n".join(
                [f"[{r.reviewer}] must_fix={r.must_fix}; issues={r.issues}; suggestions={r.suggestions}" for r in review_results]
            )

        raise RuntimeError(f"Chapter {chapter_no} failed after {max_rounds} drafts")
