#!/usr/bin/env python3
"""Score schema validity + soft expectation matches on fixtures.

Runs the mock provider by default (MOCK_LLM=1) so eval is deterministic
and does not need an API key. Prints a single SCORE line for the README.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

# Ensure project root is on path when run as script
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("MOCK_LLM", "1")
os.environ.setdefault("LLM_ENABLED", "true")

from pydantic import ValidationError  # noqa: E402

from provider import MockProvider  # noqa: E402
from schemas import ExtractResult  # noqa: E402


def score_one(fixture: dict, result: ExtractResult) -> tuple[bool, list[str]]:
    """Return (pass, reasons). Schema already validated if we got here."""
    reasons: list[str] = []
    expect = fixture.get("expect") or {}

    # Hard: schema fields already OK via ExtractResult
    if not result.summary.strip():
        reasons.append("empty summary")
    if not (0.0 <= result.confidence <= 1.0):
        reasons.append("confidence out of range")
    if result.sentiment not in ("positive", "negative", "neutral"):
        reasons.append("bad sentiment")

    if "sentiment" in expect and result.sentiment != expect["sentiment"]:
        reasons.append(f"sentiment want={expect['sentiment']} got={result.sentiment}")
    if "sentiment_in" in expect and result.sentiment not in expect["sentiment_in"]:
        reasons.append(f"sentiment not in {expect['sentiment_in']}")

    tags_any = expect.get("tags_any") or []
    if tags_any and not any(t in result.tags for t in tags_any):
        reasons.append(f"tags miss any of {tags_any}; got={result.tags}")

    tags_min = expect.get("tags_min")
    if tags_min is not None and len(result.tags) < tags_min:
        reasons.append(f"tags_min={tags_min} got={len(result.tags)}")

    return (len(reasons) == 0), reasons


async def main() -> int:
    fixtures_path = Path(__file__).with_name("fixtures.json")
    fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))
    provider = MockProvider()

    schema_ok = 0
    soft_ok = 0
    n = len(fixtures)
    details: list[dict] = []

    for fx in fixtures:
        try:
            result, _usage = await provider.extract(fx["text"])
            # re-validate dump roundtrip
            ExtractResult.model_validate(result.model_dump())
            schema_ok += 1
            passed, reasons = score_one(fx, result)
            if passed:
                soft_ok += 1
            details.append({"id": fx["id"], "pass": passed, "reasons": reasons, "result": result.model_dump()})
        except (ValidationError, Exception) as e:
            details.append({"id": fx["id"], "pass": False, "reasons": [str(e)], "result": None})

    # Primary score = schema validity rate; soft match reported separately
    schema_pct = 100.0 * schema_ok / n if n else 0.0
    soft_pct = 100.0 * soft_ok / n if n else 0.0
    # Combined eval score weights schema heavily (must be valid JSON schema)
    combined = round(0.7 * schema_pct + 0.3 * soft_pct, 1)

    print(f"fixtures={n}")
    print(f"schema_valid={schema_ok}/{n} ({schema_pct:.1f}%)")
    print(f"soft_match={soft_ok}/{n} ({soft_pct:.1f}%)")
    print(f"SCORE={combined}")
    for d in details:
        status = "PASS" if d["pass"] else "FAIL"
        print(f"  [{status}] {d['id']}: {d['reasons'] or 'ok'}")

    out = ROOT / "docs" / "eval-results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "fixtures": n,
                "schema_valid": schema_ok,
                "soft_match": soft_ok,
                "score": combined,
                "details": details,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {out}")
    return 0 if schema_ok == n else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
