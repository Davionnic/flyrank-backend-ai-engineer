# Prompt Ladder — Backend / ACRA track

**Dave Andrei Almia Gallo · Backend AI Engineer @ FlyRank · Week 2**

**Submit:** https://github.com/Davionnic/flyrank-backend-ai-engineer/blob/main/work/week-2/prompt-ladder.md

Brief: [prompt-ladder-brief.md](./prompt-ladder-brief.md)

**Track:** ACRA FastAPI backend + CVD re-encoding metrics (`Davionnic/ACRA`, `Zeref538/ACRA`). I own pipeline re-encoding design.

**Method:** Six runs (baseline + five). Exactly one named layer per version. Outputs are representative excerpts. Notes focus on what changed in the *output*.

---

## V0 — Baseline (weak)

**Prompt**
```
Write backend code for my project
```

**Output excerpt**
> Sure! Here's a generic Express/Node starter with CRUD routes for users… Also a Python Flask hello world… Let me know your stack!

| Note | |
|---|---|
| **What changed in the prompt** | Nothing — embarrassed baseline. |
| **What improved in the output** | N/A (baseline). |
| **What still failed** | Invented stacks I don't use. No ACRA, no FastAPI, no metrics. |
| **Next** | Clearer goal: one FastAPI endpoint for ACRA metrics. |

---

## V1 — Layer: clearer goal

**Prompt**
```
Write a FastAPI endpoint that runs ACRA validation metrics on a processed job.
```

**Output excerpt**
> `@app.post("/jobs/{job_id}/metrics")` calling `compute_metrics(job.original, job.corrected)` — wire from your pipeline…

| Note | |
|---|---|
| **What changed in the prompt** | Clearer goal only. |
| **What improved in the output** | Stopped inventing Express. Named FastAPI + a metrics route. |
| **What still failed** | Fake `get_job` helpers; no real metric keys or pass bars. |
| **Next** | Define audience so it stops tutoring. |

---

## V2 — Layer: defined audience

**Prompt**
```
Write a FastAPI endpoint that runs ACRA validation metrics on a processed job.
Audience: me (ACRA backend co-author) pasting into an existing FastAPI app — not a tutorial for beginners.
```

**Output excerpt**
> Skip install lecture. Add a route that loads LAB for `job_id`, calls `compute_metrics`, returns the dict. Assume app/router exist.

| Note | |
|---|---|
| **What changed in the prompt** | Defined audience only. |
| **What improved in the output** | Dropped beginner setup. Read like a patch, not a course. |
| **What still failed** | Still guessed names; ignored our real return keys. |
| **Next** | Real context from `metrics.py`. |

---

## V3 — Layer: real context

**Prompt**
```
Write a FastAPI endpoint that runs ACRA validation metrics on a processed job.
Audience: me (ACRA backend co-author) pasting into an existing FastAPI app — not a tutorial for beginners.

Context:
- code/pipeline/metrics.py has compute_metrics(...) returning de_improvement, conflict_resolution_rate, naturalness_preservation, and pass_* flags.
- Pass bars: ΔE improvement > 15 (or already accessible / post ΔE00 ≥ 20), resolution > 80%, naturalness ΔE00 < 12.
- Jobs already exist via /jobs; don't invent a new DB.
```

**Output excerpt**
> Call `compute_metrics` with job severity/cvd_type; return dict including `pass_de_improvement`, `pass_resolution_rate`, `pass_naturalness`. Reuse existing job fetch — no new SQLAlchemy models.

| Note | |
|---|---|
| **What changed in the prompt** | Real context only. |
| **What improved in the output** | Used our metric names + pass flags. Stopped inventing a DB. |
| **What still failed** | Still fuzzy on where LAB tensors live on the job object. |
| **Next** | Lock output format for clean diffs. |

---

## V4 — Layer: specified output format

**Prompt**
```
[Same as V3]

Output format:
1) Single Python code block for the route only (no prose before it)
2) Then "Assumptions" (max 5 bullets)
3) Then one example curl
```

**Output excerpt**
> One route code block → Assumptions → `curl -X POST http://localhost:8000/jobs/abc/metrics`

| Note | |
|---|---|
| **What changed in the prompt** | Specified output format only. |
| **What improved in the output** | Scannable: code, assumptions, curl. Easy to compare to V3's wall of text. |
| **What still failed** | Assumptions still hid guesses instead of marking unknowns. |
| **Next** | Try examples of good. |

---

## V5 — Layer: examples of what good looks like

**Prompt**
```
[Same as V4]

Examples of what good looks like:
- Returns only keys from compute_metrics; includes pass_* booleans; no new ORM.
- Missing job → 404 {"detail": "job not found"}.
- curl uses localhost:8000.
```

**Output excerpt**
> 404 shape and `pass_*` keys got better… but it also pasted a second "reference" implementation and OpenAPI fluff I didn't ask for.

| Note | |
|---|---|
| **What changed in the prompt** | Examples of good only. |
| **What improved in the output** | Consistent 404 + `pass_*`; curl stayed on :8000. |
| **What still failed** | **Honest: this made it worse overall.** Extra second implementation + OpenAPI padding. Examples helped a little and bloated a lot. |
| **Next** | Drop soft examples; add verification requirements in the final prompt. |

---

## Final reusable prompt (stranger-ready)

```
Write a FastAPI route that runs validation metrics for an existing job in our API.

Audience: a backend engineer pasting into an existing FastAPI app (no beginner setup).

Context:
- Metrics module (e.g. pipeline/metrics.py) exposes compute_metrics(...) returning
  de_improvement, conflict_resolution_rate, naturalness_preservation, and pass_* flags.
- Pass bars if relevant: ΔE improvement > 15 (or already accessible / post ΔE00 ≥ 20),
  resolution > 80%, naturalness ΔE00 < 12.
- Jobs already exist via /jobs (or equivalent). Do not invent a new DB/ORM.

Output format:
1) One Python code block: the route only
2) Assumptions (max 5 bullets)
3) One example curl against localhost

Verification requirements:
- Name every metric key you return; they must match compute_metrics.
- Label unknowns as UNKNOWN — do not invent storage paths or schemas.
- Do not provide a second alternate implementation.
```

**Layer scorecard:** clearer goal fixed wrong stack; audience killed tutorials; context locked real keys; format made diffs easy; **examples hurt**; verification belongs in the final prompt so strangers get honesty without bloat.

---

## Pass checklist

- [x] Six runs (V0 + V1–V5)
- [x] One named layer each
- [x] Notes describe output changes
- [x] Honest "made it worse" (V5 examples)
- [x] Final prompt works for a stranger on the track
