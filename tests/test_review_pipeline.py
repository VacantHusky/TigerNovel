from __future__ import annotations

from app.services.review_pipeline import ReviewPipeline


class DummyCfg:
    def __init__(self, name: str) -> None:
        self.name = name


class DummyReviewer:
    def __init__(self, name: str, result) -> None:
        self.config = DummyCfg(name)
        self._result = result

    def review(self, _prompt: str):
        return self._result


class DummyPolicy:
    def passed(self, results):
        return all(r.passed for r in results)


class R:
    def __init__(self, passed: bool) -> None:
        self.passed = passed


def test_review_pipeline() -> None:
    reviewers = [DummyReviewer("a", R(True)), DummyReviewer("b", R(False))]
    pipeline = ReviewPipeline(reviewers, DummyPolicy())
    results, ok = pipeline.run(lambda n: f"prompt for {n}")
    assert len(results) == 2
    assert ok is False
