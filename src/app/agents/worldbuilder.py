from __future__ import annotations

from app.agents.base import BaseAgent


WORLDBUILDER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["synopsis", "characters", "worldbuilding"],
    "properties": {
        "synopsis": {"type": "string"},
        "characters": {"type": "string"},
        "worldbuilding": {"type": "string"},
    },
}


class WorldBuilderAgent(BaseAgent):
    def build_missing(self, prompt: str) -> dict[str, str]:
        payload = self.llm.complete_json_with_schema(
            model=self.config.model,
            system_prompt=self.system_prompt,
            user_prompt=prompt,
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_output_tokens,
            schema_name="worldbuilder_output",
            schema=WORLDBUILDER_SCHEMA,
        )
        return {
            "synopsis": str(payload.get("synopsis", "")).strip(),
            "characters": str(payload.get("characters", "")).strip(),
            "worldbuilding": str(payload.get("worldbuilding", "")).strip(),
        }
