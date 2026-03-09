from __future__ import annotations

from app.domain.models import ReviewResult


class ReviewPolicy:
    def __init__(self, min_avg_score: int = 80) -> None:
        self.min_avg_score = min_avg_score

    def passed(self, results: list[ReviewResult]) -> bool:
        if not results:
            return False
        if any((not r.passed) or len(r.must_fix) > 0 for r in results):
            return False
        avg = sum(r.score for r in results) / len(results)
        return avg >= self.min_avg_score
