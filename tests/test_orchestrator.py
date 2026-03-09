from __future__ import annotations

from pathlib import Path

from app.core.orchestrator import Orchestrator
from app.domain.models import BookMeta, ReviewResult
from app.storage.fs_repo import FileRepository


class DummyPipeline:
    def __init__(self, results, ok: bool):
        self._results = results
        self._ok = ok

    def run(self, _builder):
        return self._results, self._ok


def test_build_writer_prompt_empty_values(monkeypatch) -> None:
    monkeypatch.setenv("TIGER_NOVEL_API_KEY", "test-key")
    orch = Orchestrator(Path("."))
    prompt = orch._build_writer_prompt("", "")
    assert "上下文:\n（空）" in prompt
    assert "上轮评审意见:\n（空）" in prompt


def test_resume_state_marks_final_when_passed(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("TIGER_NOVEL_API_KEY", "test-key")
    repo = FileRepository(tmp_path)
    repo.create_book(BookMeta(slug="demo", title="Demo"))
    repo.create_chapter("demo", 1, brief="x")

    orch = Orchestrator(tmp_path)
    orch.snapshots.save_draft("demo", 1, 1, "draft content")

    rr = ReviewResult(reviewer="r1", passed=True, score=90)
    pipeline = DummyPipeline([rr], ok=True)
    next_no, feedback = orch._resume_state("demo", 1, pipeline)

    assert next_no == 2
    assert feedback == ""
    assert (repo.chapter_dir("demo", 1) / "final.md").exists()
