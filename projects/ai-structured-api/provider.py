"""LLM providers: deterministic mock + OpenAI-compatible HTTP client.

Same interface. Retries + timeout on the real path. Mock never hits the network.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from schemas import ExtractResult
from settings import Settings

logger = logging.getLogger("ai_structured_api.provider")

SYSTEM_PROMPT = """You extract structured metadata from text.
Return ONLY a JSON object with keys:
  summary (string, 1-2 sentences),
  tags (array of 1-8 short lowercase tags),
  sentiment ("positive"|"negative"|"neutral"),
  confidence (number 0..1).
No markdown fences. No extra keys."""


class ProviderError(Exception):
    """Transient or permanent provider failure."""


class LLMProvider(ABC):
    name: str
    model: str

    @abstractmethod
    async def extract(self, text: str) -> tuple[ExtractResult, dict[str, int | float]]:
        """Return validated ExtractResult and usage dict (prompt_tokens, completion_tokens, cost_usd)."""


# --- Mock (deterministic) -------------------------------------------------


_POS = frozenset(
    "good great excellent amazing love happy success win best wonderful positive delight".split()
)
_NEG = frozenset(
    "bad terrible awful hate fail failed failure worst sad angry negative broken disaster".split()
)
_TAG_VOCAB = (
    "product customer support shipping quality price performance reliability "
    "security privacy update bug feature review feedback service".split()
)


def _rough_tokens(s: str) -> int:
    # crude but stable for cost estimates without a tokenizer
    return max(1, len(s) // 4)


class MockProvider(LLMProvider):
    name = "mock"
    model = "mock-deterministic-v1"

    async def extract(self, text: str) -> tuple[ExtractResult, dict[str, int | float]]:
        words = re.findall(r"[a-zA-Z']+", text.lower())
        pos = sum(1 for w in words if w in _POS)
        neg = sum(1 for w in words if w in _NEG)
        if pos > neg:
            sentiment = "positive"
        elif neg > pos:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        tags: list[str] = []
        for cand in _TAG_VOCAB:
            if cand in text.lower():
                tags.append(cand)
        if not tags:
            # stable fallback from content hash
            digest = hashlib.sha256(text.encode()).hexdigest()
            tags = [f"topic-{digest[:6]}", "general"]

        # first sentence-ish summary, capped
        summary = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)[0]
        summary = summary[:240].strip() or text[:120].strip()

        # confidence: more cue words → higher; clamp
        cue = pos + neg
        confidence = round(min(0.95, 0.55 + 0.08 * cue + (0.05 if tags[0] != "general" else 0)), 3)

        result = ExtractResult(
            summary=summary,
            tags=tags[:8],
            sentiment=sentiment,  # type: ignore[arg-type]
            confidence=confidence,
        )
        prompt_t = _rough_tokens(SYSTEM_PROMPT) + _rough_tokens(text)
        completion_t = _rough_tokens(result.model_dump_json())
        usage: dict[str, int | float] = {
            "prompt_tokens": prompt_t,
            "completion_tokens": completion_t,
            "total_tokens": prompt_t + completion_t,
            "cost_usd": 0.0,
        }
        return result, usage


# --- OpenAI-compatible ----------------------------------------------------


class OpenAICompatibleProvider(LLMProvider):
    name = "openai"

    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ProviderError("OPENAI_API_KEY is required when MOCK_LLM=0")
        self.settings = settings
        self.model = settings.openai_model
        self._timeout = settings.llm_timeout_seconds
        self._attempts = max(1, settings.llm_max_retries + 1)

    async def extract(self, text: str) -> tuple[ExtractResult, dict[str, int | float]]:
        return await self._extract_with_retry(text)

    def _retry_decorator(self):
        return retry(
            reraise=True,
            stop=stop_after_attempt(self._attempts),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
            retry=retry_if_exception_type((httpx.TimeoutException, httpx.TransportError, ProviderError)),
        )

    async def _extract_with_retry(self, text: str) -> tuple[ExtractResult, dict[str, int | float]]:
        @self._retry_decorator()
        async def _once() -> tuple[ExtractResult, dict[str, int | float]]:
            return await self._call_once(text)

        return await _once()

    async def _call_once(self, text: str) -> tuple[ExtractResult, dict[str, int | float]]:
        url = self.settings.openai_base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(url, headers=headers, json=payload)
        except httpx.TimeoutException as e:
            logger.warning("LLM timeout after %ss", self._timeout)
            raise ProviderError(f"LLM timeout after {self._timeout}s") from e
        except httpx.TransportError as e:
            logger.warning("LLM transport error: %s", e)
            raise ProviderError(f"LLM transport error: {e}") from e

        if resp.status_code >= 500:
            raise ProviderError(f"LLM server error {resp.status_code}")
        if resp.status_code == 429:
            raise ProviderError("LLM rate limited (429)")
        if resp.status_code >= 400:
            # non-retryable client errors (except 429 above)
            detail = resp.text[:300]
            raise httpx.HTTPStatusError(
                f"LLM client error {resp.status_code}: {detail}",
                request=resp.request,
                response=resp,
            )

        data = resp.json()
        try:
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            result = ExtractResult.model_validate(parsed)
        except (KeyError, IndexError, json.JSONDecodeError, ValueError) as e:
            raise ProviderError(f"LLM returned invalid structured JSON: {e}") from e

        usage_raw = data.get("usage") or {}
        prompt_t = int(usage_raw.get("prompt_tokens") or _rough_tokens(SYSTEM_PROMPT + text))
        completion_t = int(usage_raw.get("completion_tokens") or _rough_tokens(content))
        cost = (
            prompt_t / 1_000_000 * self.settings.cost_per_1m_input
            + completion_t / 1_000_000 * self.settings.cost_per_1m_output
        )
        usage: dict[str, int | float] = {
            "prompt_tokens": prompt_t,
            "completion_tokens": completion_t,
            "total_tokens": prompt_t + completion_t,
            "cost_usd": round(cost, 8),
        }
        return result, usage


def build_provider(settings: Settings) -> LLMProvider:
    if settings.mock_llm:
        return MockProvider()
    return OpenAICompatibleProvider(settings)
