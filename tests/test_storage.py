from __future__ import annotations

from pathlib import Path

from app.domain.models import BookMeta
from app.storage.fs_repo import FileRepository
from app.storage.snapshots import SnapshotStore


def test_repo_create_book_and_chapter(tmp_path: Path) -> None:
    repo = FileRepository(tmp_path)
    repo.create_book(BookMeta(slug="demo", title="Demo"))
    cdir = repo.create_chapter("demo", 1, brief="test brief")

    assert (tmp_path / "novels" / "demo" / "book.yaml").exists()
    assert (cdir / "drafts").exists()
    assert (cdir / "reviews").exists()


def test_snapshot_latest_draft_no(tmp_path: Path) -> None:
    repo = FileRepository(tmp_path)
    repo.create_book(BookMeta(slug="demo", title="Demo"))
    repo.create_chapter("demo", 1, brief="test brief")
    snapshots = SnapshotStore(repo)

    assert snapshots.latest_draft_no("demo", 1) is None

    snapshots.save_draft("demo", 1, 1, "d1")
    snapshots.save_draft("demo", 1, 3, "d3")
    snapshots.save_draft("demo", 1, 2, "d2")

    assert snapshots.latest_draft_no("demo", 1) == 3
    assert snapshots.read_draft("demo", 1, 2) == "d2"
