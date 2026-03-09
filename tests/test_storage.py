from __future__ import annotations

from pathlib import Path

from app.domain.models import BookMeta
from app.storage.fs_repo import FileRepository


def test_repo_create_book_and_chapter(tmp_path: Path) -> None:
    repo = FileRepository(tmp_path)
    repo.create_book(BookMeta(slug="demo", title="Demo"))
    cdir = repo.create_chapter("demo", 1, brief="test brief")

    assert (tmp_path / "novels" / "demo" / "book.yaml").exists()
    assert (cdir / "drafts").exists()
    assert (cdir / "reviews").exists()
