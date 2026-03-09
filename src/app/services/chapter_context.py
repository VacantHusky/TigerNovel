from __future__ import annotations

from pathlib import Path

from app.storage.fs_repo import FileRepository


class ChapterContextService:
    def __init__(self, repo: FileRepository) -> None:
        self.repo = repo

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

        prev = chapter_no - 1
        if prev >= 1:
            prev_final = bdir / "chapters" / f"{prev:03d}" / "final.md"
            if prev_final.exists():
                pieces.append("上一章定稿:\n" + prev_final.read_text(encoding="utf-8")[:4000])

        rolling = bdir / "memory" / "rolling_summary.md"
        if rolling.exists():
            pieces.append("全书滚动摘要:\n" + rolling.read_text(encoding="utf-8")[:3000])

        if brief:
            pieces.append(f"本章目标: {brief}")

        return "\n\n".join(pieces)
