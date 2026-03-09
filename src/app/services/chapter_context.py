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

    def build_context(self, slug: str, chapter_no: int, brief: str | None = None) -> str:
        bdir = self.repo.book_dir(slug)
        book = self.repo.read_yaml(bdir / "book.yaml")
        pieces: list[str] = []
        pieces.append(f"书名: {book.get('title') or slug}")
        if book.get("synopsis"):
            pieces.append(f"故事概要: {book['synopsis']}")
        if book.get("characters"):
            pieces.append(f"角色设定: {book['characters']}")
        if book.get("worldbuilding"):
            pieces.append(f"世界观: {book['worldbuilding']}")

        # 先放全书滚动摘要，再放上一章定稿（按用户要求交换顺序）
        rolling = self._read_nonempty_text(bdir / "memory" / "rolling_summary.md", 3000)
        if rolling:
            pieces.append("全书滚动摘要:\n" + rolling)

        prev = chapter_no - 1
        if prev >= 1:
            prev_final = self._read_nonempty_text(bdir / "chapters" / f"{prev:03d}" / "final.md", 4000)
            if prev_final:
                pieces.append("上一章定稿:\n" + prev_final)

        # 目标为空时不加入上下文
        if brief and brief.strip():
            pieces.append(f"本章目标: {brief.strip()}")

        return "\n\n".join(pieces)
