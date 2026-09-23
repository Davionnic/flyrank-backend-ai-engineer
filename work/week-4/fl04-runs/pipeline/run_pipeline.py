#!/usr/bin/env python3
"""FL-04 local three-step case-study pipeline (no API keys).

Steps:
  1) extract bullets from messy notes
  2) draft three-beat case (Problem / What I did / What came of it)
  3) voice-card punch (direct, plain, blunt)

Reproduce:
  cd work/week-4/fl04-runs
  python3 pipeline/run_pipeline.py
"""
from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

VOICE = "direct, plain, blunt, no buzzwords, show the work"

BUZZ = re.compile(
    r"\b(cutting[- ]edge|seamless|leverage|empower|synergy|robust|"
    r"next[- ]gen(?:eration)?|revolutionary|game[- ]changing|"
    r"best[- ]in[- ]class|world[- ]class)\b",
    re.I,
)

PREFIX = re.compile(
    r"^(?:problem|what i owned|what i did(?: / decided)?|weird decision that stuck|"
    r"failure mode to mention honestly|proof|stack|scope|politeness|live|"
    r"repo(?: path)?|dont overclaim|don't overclaim|point was|ok so|"
    r"what it demonstrates|outputs?)[:\s—-]+",
    re.I,
)


def clean(s: str) -> str:
    s = s.lstrip("- ").strip()
    s = PREFIX.sub("", s).strip()
    s = BUZZ.sub("", s)
    s = re.sub(r"\s{2,}", " ", s).strip(" -:")
    return s


def step1_extract_bullets(text: str) -> str:
    out: list[str] = []
    seen: set[str] = set()

    def add(item: str) -> None:
        item = item.strip()
        if not item:
            return
        key = item.lower()
        if key in seen:
            return
        seen.add(key)
        out.append(f"- {item}")

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            add(f"TITLE: {line.lstrip('#').strip()}")
            continue
        if line.startswith("- "):
            add(line[2:].strip())
            continue
        # high-signal lines
        if re.search(
            r"https?://|/projects/|ΔE|BE-\d+|docker|supabase|FastAPI|Pages|User-Agent|jwt|Bearer",
            line,
            re.I,
        ):
            add(line)
            continue
        if any(
            k in line.lower()
            for k in (
                "problem",
                "owned",
                "decision",
                "pain",
                "gotcha",
                "failure",
                "proof",
                "dont",
                "don't",
                "claim",
                "stack",
                "scope",
                "politeness",
                "learned",
                "live:",
                "repo",
                "endpoint",
                "output",
                "annotate",
                "pass bar",
                "confirm email",
            )
        ):
            add(line)

    if len(out) < 6:
        for raw in text.splitlines():
            line = raw.strip()
            if line and not line.startswith("#"):
                add(line)
            if len(out) >= 10:
                break

    return "# Step 1 — Extracted bullets\n\n" + "\n".join(out) + "\n"


def _score_pick(
    bullets: list[str],
    keys: tuple[str, ...],
    prefer_long: bool = True,
    exclude_substrings: tuple[str, ...] = (),
) -> str:
    scored: list[tuple[int, str]] = []
    for b in bullets:
        if b.startswith("- TITLE:"):
            continue
        low = b.lower()
        if any(x in low for x in exclude_substrings):
            continue
        hits = sum(1 for k in keys if k in low)
        if hits:
            text = clean(b)
            if len(text) < 12:
                continue
            score = hits * 10 + (len(text) if prefer_long else 0)
            if text.endswith(":"):
                score -= 20
            scored.append((score, text))
    if not scored:
        return ""
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


def step2_three_beat(slug: str, bullets_md: str) -> str:
    bullets = [ln for ln in bullets_md.splitlines() if ln.startswith("- ")]
    title = slug
    for b in bullets:
        if b.startswith("- TITLE:"):
            title = b.replace("- TITLE:", "").strip()
            break

    problem = _score_pick(
        bullets,
        ("problem", "collapse", "pain", "gotcha", "hang", "without", "wreck", "scale"),
    ) or "Notes under-specified the problem — fill before publish."

    did = _score_pick(
        bullets,
        ("owned", "annotate", "decision", "endpoint", "politeness", "docker", "fastapi", "learned", "pages workflow", "user-agent", "500ms", "bearer"),
        exclude_substrings=("problem:",),
    ) or "Built and documented the work listed in the notes."

    result = _score_pick(
        bullets,
        ("proof", "live", "pass bar", "Δe", "output", "demo", "https://", "books.json", "github.io"),
    ) or "Shipped artifacts exist in the monorepo or on a live URL."

    # avoid identical did/result
    if result == did:
        alt = _score_pick(bullets, ("https://", "repo", "path", "output", "demo", "live"))
        if alt and alt != did:
            result = alt

    body = f"""# Step 2 — Three-beat case draft

**Working title:** {title}

## Problem
{problem}

## What I did / decided
{did}

## What came of it
{result}

## Source bullets used
{chr(10).join(bullets[:14])}
"""
    return body


def step3_voice_punch(slug: str, three_beat: str) -> str:
    sections = {"problem": "", "did": "", "result": ""}
    current = None
    for ln in three_beat.splitlines():
        low = ln.strip().lower()
        if low.startswith("## problem"):
            current = "problem"
            continue
        if low.startswith("## what i did"):
            current = "did"
            continue
        if low.startswith("## what came"):
            current = "result"
            continue
        if low.startswith("## "):
            current = None
            continue
        if current and ln.strip() and not ln.startswith("#") and not ln.startswith("**"):
            sections[current] += (" " if sections[current] else "") + ln.strip()

    p, d, r = clean(sections["problem"]), clean(sections["did"]), clean(sections["result"])

    # one-liner without leftover labels
    short_p = p.split(".")[0].strip()
    short_d = d[0].lower() + d[1:] if d else "shipped the work"
    oneliner = f"{short_p}. I {short_d}. Result: {r}"
    oneliner = re.sub(r"\s{2,}", " ", oneliner)[:360]

    return f"""# Step 3 — Voice-card punch

**Voice:** {VOICE}

## Punched case

**Problem**  
{p}

**What I did / decided**  
{d}

**What came of it**  
{r}

## One-liner (for bio / card)
{oneliner}

## Buzzword scrub
Removed matches for: cutting-edge, seamless, leverage, empower, synergy, robust, next-gen, revolutionary, game-changing, best-in-class, world-class (if present).
"""


def run_one(input_path: Path, out_dir: Path) -> dict:
    t0 = time.perf_counter()
    raw = input_path.read_text(encoding="utf-8")
    slug = input_path.stem
    dest = out_dir / slug
    dest.mkdir(parents=True, exist_ok=True)

    s1 = step1_extract_bullets(raw)
    (dest / "01-bullets.md").write_text(s1, encoding="utf-8")
    s2 = step2_three_beat(slug, s1)
    (dest / "02-three-beat.md").write_text(s2, encoding="utf-8")
    s3 = step3_voice_punch(slug, s2)
    (dest / "03-voice-card.md").write_text(s3, encoding="utf-8")

    return {
        "input": input_path.name,
        "slug": slug,
        "output_dir": f"outputs/{slug}",
        "files": ["01-bullets.md", "02-three-beat.md", "03-voice-card.md"],
        "elapsed_sec": round(time.perf_counter() - t0, 4),
        "chars_in": len(raw),
        "chars_out_voice": len(s3),
        "voice_preview": clean(
            next(
                (
                    ln
                    for ln in s3.splitlines()
                    if ln and not ln.startswith("#") and not ln.startswith("**") and ln != ""
                ),
                "",
            )
        )[:120],
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description="FL-04 local case-study factory")
    ap.add_argument("--inputs", type=Path, default=root / "inputs")
    ap.add_argument("--outputs", type=Path, default=root / "outputs")
    args = ap.parse_args()
    args.outputs.mkdir(parents=True, exist_ok=True)

    inputs = sorted(args.inputs.glob("*.md"))
    if not inputs:
        raise SystemExit(f"No inputs in {args.inputs}")

    started = datetime.now(timezone.utc).isoformat()
    results = [run_one(path, args.outputs) for path in inputs]
    report = {
        "pipeline": "FL-04 local case-study factory",
        "steps": ["1 extract bullets", "2 draft three-beat case", "3 voice-card punch"],
        "voice": VOICE,
        "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "run_count": len(results),
        "runs": results,
        "label": "freshly_executed_local_pipeline",
        "reproduce": "python3 pipeline/run_pipeline.py",
    }
    report_path = root / "run-report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nWrote {report_path}")


if __name__ == "__main__":
    main()
