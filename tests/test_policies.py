from __future__ import annotations

from app.domain.models import ReviewResult
from app.domain.policies import ReviewPolicy


def test_review_policy_passed() -> None:
    policy = ReviewPolicy(min_avg_score=80)
    results = [
        ReviewResult(reviewer="a", passed=True, score=85),
        ReviewResult(reviewer="b", passed=True, score=82),
    ]
    assert policy.passed(results) is True


def test_review_policy_fail_when_must_fix() -> None:
    policy = ReviewPolicy(min_avg_score=80)
    results = [
        ReviewResult(reviewer="a", passed=True, score=95, must_fix=["x"]),
        ReviewResult(reviewer="b", passed=True, score=95),
    ]
    assert policy.passed(results) is False
