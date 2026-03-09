from __future__ import annotations

from app.agents.base import BaseAgent


class SummarizerAgent(BaseAgent):
    def summarize(self, prompt: str) -> str:
        return self.llm.complete_text(
            model=self.config.model,
            system_prompt=self.system_prompt,
            user_prompt=prompt,
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_output_tokens,
        )
