# FL-04 — Ship an Automation Workflow v2

**Dave Andrei Almia Gallo · Backend AI Engineer @ FlyRank · Week 4**

**Submit:** https://github.com/Davionnic/flyrank-backend-ai-engineer/blob/main/work/week-4/FL-04-ship-automation-workflow.md

Evidence: [fl04-runs/](./fl04-runs/) · checklist [fl04-checklist.json](./fl04-checklist.json)

---

## 1. Pipeline name + purpose

**Name:** Portfolio Case Factory (messy notes → voice-punched case)

**Purpose:** Turn messy project notes into a three-beat portfolio case study in my voice (direct, plain, blunt, no buzzwords), ready to paste into the Claude Project *Portfolio — Dave Gallo* or the site Work page.

Two layers (both real):

| Layer | What it is | Status |
|-------|------------|--------|
| **A. Human no-code path** | Claude Project → ChatGPT polish → Cursor/Grok Bot commit | Recipe below (executable by Dave/Grok Bot) |
| **B. Local reproducible path** | `fl04-runs/pipeline/run_pipeline.py` — extract → three-beat → voice punch | **Ran now** on 5 inputs; outputs committed under `fl04-runs/` |

Portal wants a working workflow + walkthrough. Layer B is the machine-checkable run. Layer A is the intended daily tool path using tools I already use.

---

## 2. Steps (≥3) with exact prompts / config

### Layer A — Human tool path (Claude Project + ChatGPT + Cursor/Grok Bot)

**Standing config (Claude Project “Portfolio — Dave Gallo”):**

```
Voice: direct, plain, blunt, no buzzwords, show the work.
Audience: backend eng manager hiring junior backend / AI-adjacent.
CTA: email gallodave.cs@gmail.com about a junior backend / AI-adjacent role.
Never invent metrics, traffic, or hit-rates. Only use numbers that appear in the notes or linked code.
Three-beat shape: Problem / What I did or decided / What came of it.
```

**Step A1 — Claude Project: extract + three-beat**

Paste messy notes. Prompt:

```
Using Project instructions, extract hard facts from the notes below.
Then draft a three-beat case: Problem / What I did or decided / What came of it.
Flag any claim that is not backed by the notes.
NOTES:
<<<paste notes>>>
```

**Step A2 — ChatGPT: failure + CTA pass**

```
Edit this three-beat case. Keep the voice blunt.
Add one honest failure / gotcha paragraph.
Do not add metrics that are not already in the draft.
End with the email CTA to gallodave.cs@gmail.com.
DRAFT:
<<<paste A1 output>>>
```

**Step A3 — Cursor / Grok Bot: file + commit**

```
Write the final case into work/week-N/<slug>-case.md (or update projects/personal-site/work.html card copy).
Commit to main with message: fl04: add <slug> case from case factory.
Do not invent links. Prefer monorepo paths and known live URLs.
```

### Layer B — Local pipeline (executed for this submission)

Config: no API keys. Pure Python heuristics + buzzword scrub.

```bash
cd work/week-4/fl04-runs
python3 pipeline/run_pipeline.py
```

| Step | File written | What it does |
|------|--------------|--------------|
| B1 Extract bullets | `outputs/<slug>/01-bullets.md` | Pull high-signal lines (URLs, ownership, problems, proof) |
| B2 Three-beat draft | `outputs/<slug>/02-three-beat.md` | Score-pick Problem / Did / Result from bullets |
| B3 Voice-card punch | `outputs/<slug>/03-voice-card.md` | Strip label prefixes, scrub buzzwords, build one-liner |

Run log: [fl04-runs/run-report.json](./fl04-runs/run-report.json) — label `freshly_executed_local_pipeline`.

---

## 3. Five runs (real inputs)

**Label for all five:** freshly invented messy notes grounded in Dave’s real work (ACRA, task-crud, supabase-auth, polite-scraper, empty-but-live). **Not** “documented from prior FlyRank work artifacts.” The *notes* are new; the *facts* match shipped repos/demos. Pipeline outputs were generated on this box when this doc was written.

Manual baseline assumption: ~25–40 min per case (read notes, draft, kill buzzwords, check links). Local pipeline wall time: &lt;1s per case; human review still needed (~5–10 min).

### Run 1 — ACRA

| | |
|--|--|
| **In** | `inputs/01-acra.md` — CVD color collapse, exclude-person skip, FastAPI+React, pass bars in metrics.py, private repo + live demo |
| **Out** | Problem: color-coded materials collapse; filters wreck images. Did: annotate people to *skip* re-encoding. Result: live demo URL. |
| **Time** | Pipeline ~0.001s · Manual estimate 35 min · After review ~8 min |
| **Failure points** | Heuristic one-liner still too long; pass bars (ΔE) did not win the “result” pick (demo URL did) — human must re-add bars before publish |

### Run 2 — task-crud-api

| | |
|--|--|
| **In** | `inputs/02-task-crud.md` — Docker Postgres primary, SQLite silent fallback, CRUD endpoints, monorepo path |
| **Out** | Problem: thinking you’re on Postgres while silently on SQLite. Did: docker compose + fallback. Result: README/Dockerfile/swagger as proof. |
| **Time** | Pipeline ~0.001s · Manual ~30 min · Review ~6 min |
| **Failure points** | No live public API URL in notes → result is “docs exist,” not a curlable prod host. Correct under “don’t invent.” |

### Run 3 — supabase-auth

| | |
|--|--|
| **In** | `inputs/03-supabase-auth.md` — FastAPI+Supabase JWT, confirm-email gotcha, monorepo path |
| **Out** | Problem: dashboard confirm-email looks like a code bug. Did: Auth API with Bearer JWT. Result: monorepo tree URL. |
| **Time** | Pipeline ~0.001s · Manual ~30 min · Review ~7 min |
| **Failure points** | “Did” line is product summary, not an ownership sentence. Human should rewrite ownership (“I wired…”) before site paste. |

### Run 4 — polite-scraper

| | |
|--|--|
| **In** | `inputs/04-polite-scraper.md` — books.toscrape sandbox, 500ms delay, UA, 60 books, books.json |
| **Out** | Problem: prove politeness without reckless crawl. Did: named educational User-Agent. Result: books.json + run-report. |
| **Time** | Pipeline ~0.001s · Manual ~25 min · Review ~5 min |
| **Failure points** | “Did” collapsed to UA only — delay/cache facts stayed in bullets but lost the three-beat. Review must re-merge politeness list. |

### Run 5 — empty-but-live

| | |
|--|--|
| **In** | `inputs/05-empty-but-live.md` — blank Pages proof, live github.io URL, later personal-site reuse |
| **Out** | Problem: content useless until Pages/HTTPS proven. Did: workflow/settings matter more than HTML. Result: personal-site reused the path. |
| **Time** | Pipeline ~0.001s · Manual ~20 min · Review ~5 min |
| **Failure points** | Easy to overclaim “portfolio.” Notes say blank on purpose — voice punch kept that if review reads Result carefully. |

---

## 4. Reproduce walkthrough

### Local (required evidence path)

```bash
git clone https://github.com/Davionnic/flyrank-backend-ai-engineer.git
cd flyrank-backend-ai-engineer/work/week-4/fl04-runs
python3 pipeline/run_pipeline.py
# inspect outputs/*/03-voice-card.md and run-report.json
```

Optional: drop a sixth messy note into `inputs/` and re-run — same three steps.

### Human tool path (daily)

1. Open Claude Project **Portfolio — Dave Gallo** with the standing voice config above.
2. Run Step A1 with a messy note file from `fl04-runs/inputs/` or new notes.
3. Paste into ChatGPT for Step A2 (failure + CTA).
4. Hand Cursor/Grok Bot Step A3 to write the file and commit.
5. Spot-check: every URL returns 200 (or is labeled private), no invented metrics.

---

## 5. Time saved + failure points summary

**Time saved (honest):**

- Drafting skeleton: ~20–30 min/case → seconds + ~5–10 min review = **~15–25 min saved per case** if you still do a human pass.
- Five cases: ~75–150 min saved vs fully manual, **not** “zero work.”
- Local pipe does not replace Claude Project for voice quality — it replaces the blank-page terror and enforces three beats.

**Failure points (keep these in the runbook):**

1. Heuristic picks can drop important facts (ACRA ΔE bars; scraper delay/cache).
2. Ownership voice (“I …”) often missing — model/human must add it.
3. Silent overlap risk if problem line also matches “did” keys — mitigated with `exclude_substrings`, still watch Run 4-style collapse.
4. No live LLM in Layer B → blunt but not clever. Layer A fixes tone.
5. Private repos (ACRA GitHub) look “broken” on curl 404 — label them; don’t delete the demo.

**Workflow vs agent (ties to FL-05):** This is a **workflow** — fixed extract → draft → punch. An agent upgrade would loop an evaluator tool that scores unsupported claims and re-searches notes up to N times.

---

## Pass checklist

- [x] Named pipeline + purpose
- [x] ≥3 steps with exact prompts/config (Layer A + Layer B)
- [x] Five runs with in/out/time/failures
- [x] Reproduce walkthrough
- [x] Time saved + failure summary
- [x] Runnable local evidence under `fl04-runs/`
