# Three Roads — Choose Your Stack with AI

**Dave Andrei Almia Gallo · Backend AI Engineer @ FlyRank · Week 4**

**Submit:** https://github.com/Davionnic/flyrank-backend-ai-engineer/blob/main/work/week-4/three-roads-stack.md

---

## Constraints I gave (and used)

1. **Free only** — no paid hosting, no paid CMS.
2. **Honest skill level** — CS undergrad; comfortable with FastAPI/Python (ACRA, W2 Task API); solid with markdown/GitHub; not a full-time frontend designer.
3. **What the portfolio must do** (from Week 1–3 maps):
   - Pages: Home → Work → About → Contact (or anchors)
   - One-line claim + ACRA case (three beats) + later FlyRank/RAG cases
   - CTAs ladder to: email `gallodave.cs@gmail.com` about a junior backend / AI-adjacent role
4. **How work must be shown:** long-form case studies, real screenshots, repo links, optional live demo links (ACRA on Vercel). Not primarily an image gallery or interactive product sandbox.
5. **Dynamic yet?** **Not yet.** v1 is static proof. Auth/DB APIs stay in separate repos (Task API, ACRA), linked out.

---

## Three stack options (simplest → most powerful)

### Option A — Simplest: Markdown → static site (Astro or plain HTML) on GitHub Pages / Cloudflare Pages
- **Build:** Write cases in MD; Astro (or hand HTML) applies Week 3 identity kit (IBM Plex Sans, `#1E3A5F` / `#0D9488`).
- **Host free:** GitHub Pages or Cloudflare Pages.
- **Backend?** No.
- **Trade-off:** Fastest ship, almost zero ops — but no CMS, no forms beyond `mailto:`, no server-side anything.

### Option B — Middle: Next.js (App Router) on Vercel free tier
- **Build:** React pages for Home/Work/About; MDX for cases; same visual kit.
- **Host free:** Vercel hobby.
- **Backend?** Not required for v1; *can* add Route Handlers later.
- **Trade-off:** Familiar if I grow into React; more moving parts and dependency churn than a static site. Easy to accidentally overbuild.

### Option C — Most powerful: FastAPI + React (or Jinja) on Railway/Render free tiers
- **Build:** Custom backend serving portfolio content; optional admin to edit cases.
- **Host free:** Render/Railway free dynos (sleep, limits).
- **Backend?** Yes — I’d maintain an app server for a site that doesn’t need one yet.
- **Trade-off:** Shows backend skill in the *portfolio shell*, but burns maintenance budget and free-tier cold starts. Work already lives in ACRA/Task API repos — duplicating a backend here is ego, not need.

---

## Pressure-test the front-runner (A)

| Question | Answer |
|---|---|
| What breaks if simplest? | No contact form DB, no logged-in “edit my case” UI. Fine — mailto + Git commits are enough for v1. |
| What must I maintain if most powerful (C)? | Uptime, deploys, env vars, free-tier sleep, security. For a brochure + case studies site: waste. |
| Finish in two weeks? | Yes for A. B maybe. C no (not if I also want BE-02/BE-03/BE-04). |
| Show work properly? | Yes — long-form MD/MDX + real screenshots + repo/demo links is exactly how backend work should be shown. |

---

## Decision (my words)

**Chosen stack: Astro (or equivalent static generator) + GitHub Pages or Cloudflare Pages — free, no backend for the portfolio itself.**

**Rejected B (Next.js/Vercel):** powerful and free, but heavier than my content needs; I’d spend time on React plumbing instead of cases. I can migrate later if I need dynamic routes.

**Rejected C (FastAPI+React portfolio):** I already prove backend skill in `w2-task-crud-api` and ACRA. Putting another backend under the marketing site fails “can I maintain this?” during internship weeks.

**Can I maintain this?** Yes — markdown files, one deploy pipeline, identity kit CSS variables. Fits a student schedule.

**Does it show my work well?** Yes — claim, three-beat cases, screenshots, GitHub links, live demos. Backend stays where it belongs: in the project repos, not forced into the portfolio host.

**Backend for the portfolio site?** **Not yet.** Honest answer.
