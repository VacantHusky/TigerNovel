from __future__ import annotations

from app.core.llm_client import LLMClient
from app.domain.models import AgentConfig


class BaseAgent:
    def __init__(self, config: AgentConfig, llm: LLMClient, system_prompt: str) -> None:
        self.config = config
        self.llm = llm
        self.system_prompt = system_prompt
