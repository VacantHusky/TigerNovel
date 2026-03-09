from __future__ import annotations

from pathlib import Path

from app.storage.fs_repo import FileRepository


class ChapterContextService:
    def __init__(self, repo: FileRepository) -> None:
        self.repo = repo

    @staticmethod
    def _read_nonempty_text(path: Path, max_chars: int) -> str | None:
        if not path.exists():
            return None
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            return None
        return text[:max_chars]

    @staticmethod
    def _compress_text(text: str, level: int) -> str:
        """压缩等级：1最详细，2中等，3最压缩。"""
        clean = text.strip()
        if not clean:
            return ""
        limit = {1: 320, 2: 180, 3: 90}.get(level, 180)
        return clean[:limit]

    def _collect_chapter_summaries(self, slug: str, chapter_no: int) -> list[tuple[int, str, str]]:
        """收集 1..chapter_no-1 的章节摘要：(序号, 标题, 摘要)。"""
        bdir = self.repo.book_dir(slug)
        out: list[tuple[int, str, str]] = []
        for no in range(1, chapter_no):
            cdir = bdir / "chapters" / f"{no:03d}"
            summary_path = cdir / "summary.md"
            summary = self._read_nonempty_text(summary_path, 4000)
            if not summary:
                continue

            title = ""
            meta_path = cdir / "chapter.yaml"
            if meta_path.exists():
                meta = self.repo.read_yaml(meta_path) or {}
                title = (meta.get("title") or "").strip()

            out.append((no, title, summary))
        return out

    def _build_dynamic_rolling_summary(self, slug: str, chapter_no: int) -> str:
        """动态构建全书滚动摘要：
        - 最近章节：逐章（压缩等级低）
        - 更久远章节：5章合并
        - 最久远章节：10章合并
        """
        entries = self._collect_chapter_summaries(slug, chapter_no)
        if not entries:
            return ""

        # 最近 3 章单章保留（等级1）
        recent = entries[-3:]
        older = entries[:-3]

        # 更久远：近端 older 最多 20 章按 5 章合并（等级2）
        mid_pool = older[-20:]
        far_pool = older[:-20]

        parts: list[str] = []

        # 最久远：10章合并（等级3）
        for i in range(0, len(far_pool), 10):
            chunk = far_pool[i:i + 10]
            if not chunk:
                continue
            start, end = chunk[0][0], chunk[-1][0]
            merged = "\n".join([f"第{n:03d}章 {t}".strip() + f"：{s}" for n, t, s in chunk])
            parts.append(f"[L3 第{start:03d}-第{end:03d}章] " + self._compress_text(merged, 3))

        # 中等久远：5章合并（等级2）
        for i in range(0, len(mid_pool), 5):
            chunk = mid_pool[i:i + 5]
            if not chunk:
                continue
            start, end = chunk[0][0], chunk[-1][0]
            merged = "\n".join([f"第{n:03d}章 {t}".strip() + f"：{s}" for n, t, s in chunk])
            parts.append(f"[L2 第{start:03d}-第{end:03d}章] " + self._compress_text(merged, 2))

        # 最近：逐章（等级1）
        for n, t, s in recent:
            head = f"第{n:03d}章 {t}".strip()
            parts.append(f"[L1 {head}] " + self._compress_text(s, 1))

        return "\n".join(parts).strip()

    def build_context(self, slug: str, chapter_no: int, chapter_title: str | None = None) -> str:
        bdir = self.repo.book_dir(slug)
        book = self.repo.read_yaml(bdir / "book.yaml")
        pieces: list[str] = []

        # 当前章节序号与标题
        cur_title = chapter_title.strip() if chapter_title and chapter_title.strip() else "（未命名）"
        pieces.append(f"当前章节: 第{chapter_no:03d}章 {cur_title}")

        pieces.append(f"书名: {book.get('title') or slug}")
        if book.get("synopsis"):
            pieces.append(f"故事概要: {book['synopsis']}")
        if book.get("characters"):
            pieces.append(f"角色设定: {book['characters']}")
        if book.get("worldbuilding"):
            pieces.append(f"世界观: {book['worldbuilding']}")

        # 先放全书滚动摘要，再放上一章定稿
        rolling = self._build_dynamic_rolling_summary(slug, chapter_no)
        if rolling:
            pieces.append("全书滚动摘要:\n" + rolling)

        prev = chapter_no - 1
        if prev >= 1:
            prev_final = self._read_nonempty_text(bdir / "chapters" / f"{prev:03d}" / "final.md", 4000)
            if prev_final:
                pieces.append("上一章定稿:\n" + prev_final)

        return "\n\n".join(pieces)
