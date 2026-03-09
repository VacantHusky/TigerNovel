from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from app.domain.models import BookMeta, ChapterMeta


class FileRepository:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.novels_root = root / "novels"
        self.novels_root.mkdir(parents=True, exist_ok=True)

    def book_dir(self, slug: str) -> Path:
        return self.novels_root / slug

    def chapter_dir(self, slug: str, chapter_no: int) -> Path:
        return self.book_dir(slug) / "chapters" / f"{chapter_no:03d}"

    def create_book(self, meta: BookMeta) -> Path:
        bdir = self.book_dir(meta.slug)
        (bdir / "chapters").mkdir(parents=True, exist_ok=True)
        (bdir / "memory").mkdir(parents=True, exist_ok=True)
        (bdir / "outlines").mkdir(parents=True, exist_ok=True)
        self.write_yaml(bdir / "book.yaml", meta.model_dump(mode="json"))
        (bdir / "memory" / "rolling_summary.md").write_text("# Rolling Summary\n\n", encoding="utf-8")
        return bdir

    def create_chapter(self, slug: str, chapter_no: int, title: str | None = None) -> Path:
        cdir = self.chapter_dir(slug, chapter_no)
        (cdir / "drafts").mkdir(parents=True, exist_ok=True)
        (cdir / "reviews").mkdir(parents=True, exist_ok=True)
        meta = ChapterMeta(chapter_no=chapter_no, title=title)
        self.write_yaml(cdir / "chapter.yaml", meta.model_dump(mode="json"))
        return cdir

    @staticmethod
    def write_yaml(path: Path, payload: dict[str, Any]) -> None:
        path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")

    @staticmethod
    def read_yaml(path: Path) -> dict[str, Any]:
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    @staticmethod
    def write_json(path: Path, payload: dict[str, Any]) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
