# Voice Card & Case Studies

**Dave Andrei Almia Gallo · Backend AI Engineer @ FlyRank · Week 2**

Brief: [voice-card-case-studies-brief.md](./voice-card-case-studies-brief.md)

Audience: a backend engineering manager at a company shipping AI features  
Action: email me about a junior backend / AI-adjacent role — `gallodave.cs@gmail.com`

---

## Voice card

**direct, plain, blunt, no buzzwords, show the work**

*(Add this to your Claude Project as a standing instruction.)*

---

## Bio

Dave Andrei Almia Gallo — CS undergrad at OLFU, Backend AI Engineer at FlyRank. I ship backend services that put AI behind real checks. Co-building ACRA, a color-accessibility system for CVD users.

## Contact / CTA

Backend engineering manager shipping AI features: if this standard shows up in the work, email me about a junior backend / AI-adjacent role — `gallodave.cs@gmail.com`

GitHub: [Davionnic](https://github.com/Davionnic) · ACRA demo: [acra-sandy.vercel.app](https://acra-sandy.vercel.app)

---

## Case 1 — ACRA (Adaptive Color Re-Encoding)

**Problem**  
Color-coded public materials (signs, maps, posters) collapse for red-green color-blind viewers. Global filters wreck the whole image; redesign can't scale to arbitrary uploads.

**What I did / decided**  
I owned pipeline re-encoding design and frontend design. We annotate people as `exclude-person` so the model can detect them and *skip* re-encoding — skin/face stay natural. It feels backwards until you say it: you label so you can leave them alone. We kept that approach because we lacked time to redesign annotation.

**What came of it**  
Working system (FastAPI + React; demo [acra-sandy.vercel.app](https://acra-sandy.vercel.app)). Locked pass bars in `code/pipeline/metrics.py`: ΔE improvement > 15, conflict resolution > 80%, naturalness ΔE₀₀ < 12. No fabricated hit-rate — those are the bars we designed the pipeline to pass.

Repo: [Zeref538/ACRA](https://github.com/Zeref538/ACRA) (private; co-author)

---

## Before / after (generic AI → edited)

**Before (generic AI)**  
"ACRA is a cutting-edge, results-driven accessibility solution leveraging AI to empower CVD users with seamless, inclusive visual experiences."

**After (edited)**  
"ACRA re-encodes images so red-green color-blind viewers can tell conflicting colors apart — without painting over people's skin."

---

## Sitemap note

Week 2 ships **ACRA only**. More portfolio pieces can be added as separate cases when ready.
