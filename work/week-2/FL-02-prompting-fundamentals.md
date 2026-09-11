# FL-02 — Prompting Fundamentals on Real Tasks

**Dave Andrei Almia Gallo · Backend AI Engineer @ FlyRank · Week 2**

**Submit:** https://github.com/Davionnic/flyrank-backend-ai-engineer/blob/main/work/week-2/FL-02-prompting-fundamentals.md

Assignment: Prompting Fundamentals on Real Tasks v2 (FL-02)

---

## Tutorial note

Anthropic Academy / AI Fluency: **20 modules completed** (per FL-01 toolkit). Prompt-engineering basics practiced there before this log; this FL-02 run applies the named techniques on a real FL-01 target task.

---

## FL-01 target task used

**Target 1 — Backend + AI integration code (collaborate)**  
From FL-01: write backend + AI integration code (services, prompts, eval harnesses) with 0 unverified claims and critical paths I can explain.

**Concrete ask for this log:** draft a FastAPI route that runs ACRA `compute_metrics` on an existing job and returns pass/fail against locked bars — paste-ready for the ACRA FastAPI app.

---

## V0 — Naive one-liner (baseline)

**Prompt**
```
Write backend code for metrics
```

**Output excerpt**
> Here's a Node/Express metrics middleware that tracks request latency… Also a Prometheus counter example…

**Note:** Output ignored ACRA entirely and invented a Node stack. Useless for the real task — baseline embarrassment.

---

## V1 — Technique: role assignment

**Prompt**
```
You are a senior FastAPI engineer reviewing a junior's ACRA backend.
Write the metrics route they should add.
```

**Output excerpt**
> As a reviewer I'd expect a clean `@router.post("/jobs/{id}/metrics")` that calls your pipeline metrics helper and returns JSON…

**Note (output diff):** Role shifted tone from random tutorial to "PR review" shape — still vague on our real `compute_metrics` keys, but stopped suggesting Express.

---

## V2 — Technique: context and motivation

**Prompt**
```
You are a senior FastAPI engineer reviewing a junior's ACRA backend.
Write the metrics route they should add.

Context: ACRA re-encodes images for CVD users. metrics.py compute_metrics returns de_improvement, conflict_resolution_rate, naturalness_preservation, pass_* flags. Pass bars: ΔE > 15 (or accessible / post ΔE00 ≥ 20), resolution > 80%, naturalness < 12. Jobs already exist via /jobs — don't invent a DB.
Motivation: I need a route I can paste and defend in review — no unverified numbers.
```

**Output excerpt**
> Route calls `compute_metrics`, returns those keys and pass_* booleans, reuses job fetch…

**Note (output diff):** Started using our real metric names and “no new DB.” Motivation cut motivational fluff; stayed technical.

---

## V3 — Technique: few-shot examples

**Prompt**
```
[Same as V2]

Examples:
Good response shape:
1) one code block (route only)
2) max 5 assumption bullets
3) one curl

Good 404: {"detail": "job not found"}
Bad: second alternate implementation, beginner install guide, inventing SQLAlchemy models.
```

**Output excerpt**
> Single route block + short assumptions + curl to :8000. 404 shape matched. Briefly tempted to add OpenAPI schema prose — kept shorter than without the bad examples.

**Note (output diff):** Format snapped to code/assumptions/curl. Few-shots reduced tutorial padding vs V2. (Contrast with Prompt Ladder V5 where soft examples bloated — here “bad” examples helped more than “good” alone.)

---

## V4 — Technique: output structure

**Prompt**
```
[Same as V3]

Output structure (mandatory):
## Route
(code fence)
## Assumptions
(bullets, ≤5)
## Curl
(one line)
## Unknowns
(label anything not in context as UNKNOWN — no invented paths)
```

**Output excerpt**
> Four clear sections. Unknowns listed: exact job blob field for LAB arrays = UNKNOWN.

**Note (output diff):** Structure made the UNKNOWN explicit instead of hiding a fake `job.lab_path`. Easier to review than V3’s looser assumptions.

---

## V5 — Technique: step decomposition

**Prompt**
```
[Same as V4]

Solve in steps, show briefly:
Step 1: Identify inputs from existing job object (or mark UNKNOWN).
Step 2: Call compute_metrics with correct arguments.
Step 3: Map return dict to HTTP JSON including pass_*.
Step 4: Error cases (404 missing job; 500 metrics failure).
Then produce the Route / Assumptions / Curl / Unknowns sections.
```

**Output excerpt**
> Steps listed first, then the four sections. Error cases included 404 + 500. Still UNKNOWN on LAB storage — correctly not invented.

**Note (output diff):** Decomposition surfaced error handling V4 skipped. Didn’t invent paths. Best paste candidate so far.

---

## Cross-model comparison (final prompt on Claude vs ChatGPT)

**Final prompt used:** V5 prompt (role + context/motivation + few-shot + structure + step decomposition).

| Dimension | Claude (Project: Portfolio — Dave Gallo) | ChatGPT |
|---|---|---|
| **Tone** | Blunt, patch-oriented; matched tutor instructions | More polite preamble (“Happy to help…”), then solid code |
| **Accuracy** | Used real metric key names; labeled UNKNOWN for job blob | Also used pass_* keys; once guessed `job.artifacts["lab"]` without marking unknown |
| **Structure** | Followed ## Route / Assumptions / Curl / Unknowns tightly | Followed headings but added an extra “Next steps” section |
| **Failure points** | Won’t finish paste-ready without job schema (honest) | Over-confident on storage path; needs a human check before merge |

**Honest take:** Claude failed safer (UNKNOWN). ChatGPT looked more “complete” but smuggled a guess — worse for our “never invent numbers/paths” rule. For this task, Claude’s refusal to invent is the better failure mode.

*Method: final prompt run in Claude Project; ChatGPT run in parallel session with the same pasted prompt. Excerpts summarized above.*

---

## Final reusable template (stranger-ready)

```
You are a senior FastAPI engineer reviewing a junior backend PR.

Task: Write one route that runs validation metrics for an existing job.

Context:
- A metrics function compute_metrics(...) returns de_improvement, conflict_resolution_rate,
  naturalness_preservation, and pass_* booleans.
- Pass bars if relevant: ΔE improvement > 15 (or already accessible / post ΔE00 ≥ 20),
  resolution > 80%, naturalness ΔE00 < 12.
- Jobs already exist in the app. Do not invent a new DB/ORM.
- Motivation: paste-ready code that can be defended in review; no unverified claims.

Examples:
- Good: one route, real metric keys, 404 {"detail":"job not found"}, no second implementation.
- Bad: beginner install guide, alternate implementations, invented file paths.

Output structure:
## Route
## Assumptions (≤5)
## Curl
## Unknowns (label anything missing as UNKNOWN)

Steps (brief):
1) Inputs from job or UNKNOWN
2) Call compute_metrics
3) Map return dict + pass_* to JSON
4) 404 / 500 cases
Then produce the four sections.
```

---

## Pass checklist

- [x] Real FL-01 target task (Target 1 — backend + AI integration)
- [x] Naive + ≥5 iterations with named techniques (role, context/motivation, few-shot, output structure, step decomposition)
- [x] Notes describe output differences
- [x] Cross-model comparison with specific observations
- [x] Reusable final template without personal-only context
