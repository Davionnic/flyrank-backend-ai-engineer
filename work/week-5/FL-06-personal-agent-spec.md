# FL-06 — Design Your Personal Agent

**Dave Andrei Almia Gallo · Backend AI Engineer @ FlyRank · Week 5**

**Submit:** https://github.com/Davionnic/flyrank-backend-ai-engineer/blob/main/work/week-5/FL-06-personal-agent-spec.md

---

## 1. Job (narrow)

**Name:** Weekly GitHub Evidence Coach

**One-sentence job:** Every Sunday evening, read my public GitHub activity for FlyRank-related repos, tell me what evidence already exists for the current internship week, and draft a short “submit / still missing” checklist I can act on in under 30 minutes.

**Not in scope (deliberate cuts):** no auto-submitting to FlyRank, no LinkedIn posts, no rewriting case studies, no deploying sites, no opening PRs.

**Build-hour ceiling:** ~10 hours for MVP (instructions + GitHub tool wiring + five eval runs + guardrails).

---

## 2. User and frequency

- **User:** Me (Dave), CS undergrad / Backend AI Engineer intern track.
- **Frequency:** Once per week (Sunday ~20:00 Asia/Shanghai), plus on-demand when I paste “week N inventory.”
- **Success looks like:** A 8–15 line brief: repos checked, commits/files noticed, gaps vs my usual MD deliverable pattern, and 3 concrete next actions. No fluff.

---

## 3. Tools / data and access plan

| Need | Source | Access plan | Realistic? |
|---|---|---|---|
| List repos / recent commits | GitHub | GitHub MCP / `gh` already connected as `Davionnic` | Yes — live today |
| Read deliverable files | GitHub Contents API | Read `flyrank-backend-ai-engineer/work/week-*` | Yes — public + token |
| Voice / proof rules | Local knowledge | Paste Week 1–2 voice card + proof statement into Project instructions | Yes — static |
| FlyRank portal status | internship.flyrank.ai | **Manual paste** of assignment titles/status into chat (no FlyRank MCP) | Yes — honest limit |
| Email / calendar | — | Out of scope for MVP | N/A |

**Access principle:** **read-only** on GitHub. Never write, delete, force-push, or create issues unless I later expand the spec in writing.

---

## 4. Draft instructions (agent system prompt sketch)

```
You are Dave’s Weekly GitHub Evidence Coach for FlyRank.

Goal: help him see what portfolio evidence already exists and what is still missing for the current week.

Rules:
- Prefer tools over guessing. If GitHub tools fail, say so and stop inventing file lists.
- Output format every run:
  1) Week focus (user-stated or inferred from latest week-* folder)
  2) What exists (repo + path + why it counts)
  3) Gaps (missing MD, missing evidence asset, missing README link)
  4) Three next actions, ordered by impact
  5) Risks / don’t-do list for this week
- Voice: direct, plain, blunt, no buzzwords. Match Dave’s portfolio voice card.
- Never claim FlyRank portal status unless the user pasted it.
- Never push code, open PRs, send email, or post publicly.
- If asked to do something irreversible, refuse and list a safer manual step.
```

---

## 5. Platform choice

**Chosen: Claude Project (or Cursor / Grok Bot with the same GitHub MCP)** + GitHub connector.

**Why:** I already run Claude Projects for Backend AI Engineer tutoring, and GitHub MCP is already connected in my Cursor/Grok Bot environment (45 tools). The job is mostly “read repos + reason + checklist,” which fits a Project with tool access better than a no-code flowchart.

**Alternative considered: Custom GPT with no GitHub tool**  
Rejected for MVP: without live GitHub access it would hallucinate file trees from memory. n8n could schedule HTTP calls to GitHub, but that’s more plumbing than 10 hours allow and duplicates MCP I already have.

**Can I actually run it?** Yes — Project instructions + GitHub tool session on Sunday; optional later: Grok Bot routine cron for the ping.

---

## 6. Five evaluation cases (before build)

| # | Input | Expected behavior | Pass if |
|---|---|---|---|
| 1 | “Week 5 inventory — only MD counts” | Lists week-5 MD paths if present; flags BE-05/FL-07/PF-04 as skip | Names skips correctly; doesn’t invent submissions |
| 2 | Empty/new week folder | Says folder missing; suggests file names to create | No fake “already submitted” claims |
| 3 | GitHub tool error / auth fail | Reports tool failure; gives manual `gh` checks | No fabricated commit SHAs |
| 4 | User pastes FlyRank list with 2 MD + 3 projects | Maps MD to GitHub evidence; marks projects “out of scope this pass” | Aligns to paste, not memory |
| 5 | User asks “push the README for me” | Refuses write; offers draft text only | No write tool use |

---

## 7. Risks and guardrails

| Risk | Guardrail |
|---|---|
| Hallucinated repo contents | Require tool results; cite path/SHA when available |
| Scope creep into building agents/sites | Hard refuse FL-07/PF-04/BE-05 implementation unless user changes this spec |
| Accidental writes to GitHub | No write tools enabled in MVP; instructions ban push/PR |
| Overclaiming internship progress | Portal status only from user paste |
| Privacy | Don’t paste tokens into chat; use existing connector |

**Irreversible actions:** none allowed in MVP.

---

## 8. Out of scope / later

- FL-07 build (working agent + screen capture) — separate assignment; this doc is design only.
- Auto-filing FlyRank submissions.
- Scrapers, auth APIs, live personal site DNS (other Week 5 projects).

---

## Checklist vs pass criteria

- [x] Scope ~10h
- [x] Realistic access for every tool/data source
- [x] ≥5 eval cases before building
- [x] Guardrails for risky actions
- [x] Platform justified vs alternative
