from __future__ import annotations

from app.agents.base import BaseAgent


class GoalAgent(BaseAgent):
    def draft_goal(self, context: str) -> str:
        """生成简要本章目标（尽量一句话）。"""
        prompt = (
            "请基于以下内容生成“本章目标”。要求：\n"
            "1) 简短（建议 10~40 字）\n"
            "2) 聚焦本章剧情推进\n"
            "3) 只输出目标文本，不要解释\n\n"
            f"上下文:\n{context}"
        )
        return self.llm.complete_text(
            model=self.config.model,
            system_prompt=self.system_prompt,
            user_prompt=prompt,
            temperature=self.config.temperature,
            max_output_tokens=min(self.config.max_output_tokens, 120),
        ).strip()
