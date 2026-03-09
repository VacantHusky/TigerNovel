from __future__ import annotations

from app.agents.reviewer import ReviewerAgent
from app.domain.models import ReviewResult
from app.domain.policies import ReviewPolicy


class ReviewPipeline:
    def __init__(self, reviewers: list[ReviewerAgent], policy: ReviewPolicy) -> None:
        self.reviewers = reviewers
        self.policy = policy

    def run(self, review_prompt_builder) -> tuple[list[ReviewResult], bool]:
        results: list[ReviewResult] = []
        for r in self.reviewers:
            prompt = review_prompt_builder(r.config.name)
            results.append(r.review(prompt))
        return results, self.policy.passed(results)
