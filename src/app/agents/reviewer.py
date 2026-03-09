from __future__ import annotations

import json

from app.agents.base import BaseAgent
from app.domain.models import ReviewResult


def _normalize_list_items(value) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        value = [value]
    out: list[str] = []
    for item in value:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict):
            out.append(json.dumps(item, ensure_ascii=False))
        else:
            out.append(str(item))
    return out


REVIEW_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["reviewer", "passed", "score", "issues", "must_fix", "suggestions"],
    "properties": {
        "reviewer": {"type": "string"},
        "passed": {"type": "boolean"},
        "score": {"type": "integer", "minimum": 0, "maximum": 100},
        "issues": {"type": "array", "items": {"type": "string"}},
        "must_fix": {"type": "array", "items": {"type": "string"}},
        "suggestions": {"type": "array", "items": {"type": "string"}},
    },
}


class ReviewerAgent(BaseAgent):
    def review(self, prompt: str) -> ReviewResult:
        payload = self.llm.complete_json_with_schema(
            model=self.config.model,
            system_prompt=self.system_prompt,
            user_prompt=prompt,
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_output_tokens,
            schema_name=f"review_result_{self.config.name}",
            schema=REVIEW_SCHEMA,
        )
        payload.setdefault("reviewer", self.config.name)
        payload.setdefault("passed", False)
        payload.setdefault("score", 0)
        payload["issues"] = _normalize_list_items(payload.get("issues"))
        payload["must_fix"] = _normalize_list_items(payload.get("must_fix"))
        payload["suggestions"] = _normalize_list_items(payload.get("suggestions"))
        payload.setdefault("raw", payload.copy())
        return ReviewResult(**payload)
