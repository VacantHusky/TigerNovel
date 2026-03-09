from __future__ import annotations

import re
from pathlib import Path

from app.domain.models import ReviewResult
from app.storage.fs_repo import FileRepository


_DRAFT_RE = re.compile(r"^draft_(\d{3})\.md$")


class SnapshotStore:
    def __init__(self, repo: FileRepository) -> None:
        self.repo = repo

    def save_draft(self, slug: str, chapter_no: int, draft_no: int, content: str) -> Path:
        cdir = self.repo.chapter_dir(slug, chapter_no)
        dpath = cdir / "drafts" / f"draft_{draft_no:03d}.md"
        dpath.write_text(content, encoding="utf-8")
        return dpath

    def read_draft(self, slug: str, chapter_no: int, draft_no: int) -> str:
        cdir = self.repo.chapter_dir(slug, chapter_no)
        dpath = cdir / "drafts" / f"draft_{draft_no:03d}.md"
        return dpath.read_text(encoding="utf-8")

    def latest_draft_no(self, slug: str, chapter_no: int) -> int | None:
        cdir = self.repo.chapter_dir(slug, chapter_no)
        ddir = cdir / "drafts"
        if not ddir.exists():
            return None
        nums: list[int] = []
        for p in ddir.glob("draft_*.md"):
            m = _DRAFT_RE.match(p.name)
            if m:
                nums.append(int(m.group(1)))
        return max(nums) if nums else None

    def save_review(self, slug: str, chapter_no: int, draft_no: int, review: ReviewResult) -> Path:
        cdir = self.repo.chapter_dir(slug, chapter_no)
        rpath = cdir / "reviews" / f"review_{review.reviewer}_draft_{draft_no:03d}.json"
        self.repo.write_json(rpath, review.model_dump(mode="json"))
        return rpath

    def save_final(self, slug: str, chapter_no: int, content: str) -> Path:
        cdir = self.repo.chapter_dir(slug, chapter_no)
        fpath = cdir / "final.md"
        fpath.write_text(content, encoding="utf-8")
        return fpath
