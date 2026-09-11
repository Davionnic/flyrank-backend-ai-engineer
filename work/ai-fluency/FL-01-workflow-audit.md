# FL-01 — AI Workflow Audit

**Dave Andrei Almia Gallo · CS undergrad (OLFU) · Backend AI Engineer @ FlyRank · Week 1**

Classification framework: Ethan Mollick's "On-boarding your AI Intern" — *just me / delegate to AI with review / collaborate with AI / fully automate.*

## 1. Workflow audit (13 recurring tasks from my real week)

| # | Task | Classification | Rationale (one line) |
|---|---|---|---|
| 1 | Framing my FlyRank backend/AI problem (API contract, failure mode, cost of a wrong call) | **Just me** | The internship grades *my* judgment; if AI frames the problem, I learn nothing and can't defend tradeoffs to reviewers. |
| 2 | Verifying numbers, logs, and claims before they land in a PR or writeup | **Just me** | Never let AI decide what is true — I only trust what I reproduced from runs/logs. |
| 3 | Writing backend + AI integration code (services, prompts, eval harnesses, data pipelines) | **Collaborate** | AI drafts fast, but I catch domain gotchas (auth, idempotency, bad defaults, leakage into evals) that need my system knowledge. |
| 4 | Debugging env/setup (deps, Docker, wrong interpreter, git conflicts, CI failures) | **Delegate with review** | AI resolves these far faster than I do; I review the fix and confirm before running anything destructive. |
| 5 | Learning new backend/AI concepts (RAG pitfalls, eval metrics, rate limits, schema design) | **Collaborate** | AI explains at my level and I test understanding by re-explaining / applying it; reading docs alone is slower, but I must do the re-explaining myself or it doesn't stick. |
| 6 | Writing commit messages, API docs, and READMEs | **Delegate with review** | Low-risk, well-defined from the diff/content; I review for accuracy since docs that overstate results violate my "show my work honestly" claim. |
| 7 | School / thesis writing (ACRA or coursework sections) | **Collaborate** | AI helps structure and tighten prose, but the methodology and results are mine and my adviser checks my voice. |
| 8 | Studying for certifications (Anthropic Academy, Coursera modules) | **Just me** | The point is certified *personal* competence; AI summaries would let me pass without learning, which defeats the credential. |
| 9 | Portfolio updates (project blurbs, case-study copy, metrics) | **Collaborate** | AI drafts copy from my project facts; I correct numbers and tone because interviewers will probe anything on that page. |
| 10 | Formatting/converting documents (notes → tables, markdown, diagrams) | **Fully automate** | Zero-judgment transformation with instantly checkable output; my time adds nothing. |
| 11 | First-pass summaries of long reading (specs, lane guides, papers) | **Delegate with review** | AI's summary tells me where to focus, then I read the load-bearing sections myself — full reads of everything don't fit a packed week. |
| 12 | Scanning job/internship postings for fit | **Delegate with review** | AI filters against my profile fast; I make the final apply/skip call since fit is partly about what I want, not just keywords. |
| 13 | Weekly planning across internship + school deadlines | **Collaborate** | AI is good at surfacing conflicts and sequencing, but only I know real priorities and my energy levels. |

**Honestly "just me" (with reasons):** #1 (problem framing — graded judgment), #2 (truth verification — the anti-hallucination discipline the track is built on), #8 (cert study — the credential must reflect real personal competence).

## 2. Toolkit evidence

- Claude account: active (claude.ai)
- ChatGPT account: active
- Cursor / Grok Bot: in use
- Anthropic Academy: enrolled in **AI Fluency**, **20 modules completed**
- Claude Project: configured *(custom instructions below)*

## 3. Claude Project custom instructions (as configured)

> **Who I am:** Dave Andrei Almia Gallo, CS undergraduate at Our Lady of Fatima University
> (OLFU), Backend AI Engineer at FlyRank on the AI Fluency track. GitHub: Davionnic ·
> repo: flyrank-backend-ai-engineer.
>
> **Tone preferences:** plain words first, then the technical term in parentheses.
> Explain like a mentor, not a lecture. Be blunt about what's wrong. When I ask for
> code, add short comments explaining the why.
>
> **Current goals (8 weeks):** ship honest FlyRank backend/AI work (clear APIs, solid
> evals, no leakage, careful claims), finish the AI Fluency track, keep Anthropic
> Academy progress honest, and refine my portfolio around one claim: "I build backend
> systems that use AI carefully — and I show my work."
>
> **Standing rules:** never invent numbers — if I haven't given you the data, say so
> and tell me what to run. Flag any claim in my drafts that sounds causal or
> overclaims. Push back when I try to skip verification.

## 4. Three target tasks for FL-02 → FL-04 (with "done well" definitions)

**Target 1 — Backend + AI integration code (from task #3, collaborate).**
Done well means: the service or notebook runs cleanly after AI assistance; every number printed was verified by actually executing the code (zero unverified claims); and I can explain every important line out loud without notes — measured by re-explaining the critical path and finding no gaps.

**Done-well metric:** 0 execution errors, 0 unverified claims, 100% of critical paths I can explain unaided.

**Target 2 — First-pass summaries of long reading (from task #11, delegate with review).**
Done well means: the AI summary identifies the 3–5 sections worth reading in full; after my own read of those sections I find no critical point the summary missed or misstated (spot-check against the source); and the whole cycle takes under 30 minutes per document versus ~90 minutes for an unaided full read.

**Done-well metric:** ≤30 min per document, 0 critical misses found on spot-check, sections-to-read list I actually used.

**Target 3 — Portfolio / case-study copy (from task #9, collaborate).**
Done well means: every metric in the copy traces to a real artifact (repo, notebook, or report I can open); the copy passes a pressure-test against my proof statement ("does this earn its place?"); and it reads in my voice — verified by a friend or tutor confirming it doesn't sound templated.

**Done-well metric:** 100% of numbers source-traceable, passes the pressure-test with ≤1 revision, third-party voice check passed.
