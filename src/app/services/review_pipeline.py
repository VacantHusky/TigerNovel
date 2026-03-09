from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from app.agents.reviewer import ReviewerAgent
from app.domain.models import ReviewResult
from app.domain.policies import ReviewPolicy


class ReviewPipeline:
    def __init__(self, reviewers: list[ReviewerAgent], policy: ReviewPolicy) -> None:
        self.reviewers = reviewers
        self.policy = policy

    def run(self, review_prompt_builder) -> tuple[list[ReviewResult], bool]:
        prompts = {r.config.name: review_prompt_builder(r.config.name) for r in self.reviewers}
        by_name = {r.config.name: r for r in self.reviewers}

        results_map: dict[str, ReviewResult] = {}
        with ThreadPoolExecutor(max_workers=max(1, len(self.reviewers))) as ex:
            futures = {
                ex.submit(by_name[name].review, prompt): name
                for name, prompt in prompts.items()
            }
            for fut, name in futures.items():
                results_map[name] = fut.result()

        # keep reviewer order stable
        results = [results_map[r.config.name] for r in self.reviewers]
        return results, self.policy.passed(results)
