from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    name: str
    model: str
    temperature: float = 0.7
    max_output_tokens: int = 2000
    system_prompt_file: str


class BookMeta(BaseModel):
    slug: str
    title: str | None = None
    synopsis: str | None = None
    characters: str | None = None
    worldbuilding: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChapterMeta(BaseModel):
    chapter_no: int
    brief: str | None = None
    status: str = "drafting"


class ReviewResult(BaseModel):
    reviewer: str
    passed: bool
    score: int = Field(ge=0, le=100)
    issues: list[str] = Field(default_factory=list)
    must_fix: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class PathBundle(BaseModel):
    root: Path
    book_dir: Path
    chapters_dir: Path
