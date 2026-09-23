"""Request/response schemas for structured LLM extraction."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


Sentiment = Literal["positive", "negative", "neutral"]


class ExtractRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20_000, description="Raw text to analyze")

    @field_validator("text")
    @classmethod
    def strip_and_require(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("text must not be empty or whitespace-only")
        return cleaned


class ExtractResult(BaseModel):
    summary: str = Field(..., min_length=1, max_length=500)
    tags: list[str] = Field(..., min_length=1, max_length=12)
    sentiment: Sentiment
    confidence: float = Field(..., ge=0.0, le=1.0)

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, tags: list[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for t in tags:
            cleaned = t.strip().lower()
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            out.append(cleaned[:40])
        if not out:
            raise ValueError("tags must contain at least one non-empty tag")
        return out[:12]


class ExtractResponse(BaseModel):
    result: ExtractResult
    provider: Literal["mock", "openai"]
    model: str
    usage: dict[str, int | float]
