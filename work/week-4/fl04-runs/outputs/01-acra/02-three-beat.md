# Step 2 — Three-beat case draft

**Working title:** messy notes — ACRA (Adaptive Color Re-Encoding)

## Problem
signs maps posters with color codes collapse for those viewers. global filters wreck the whole image. redesign doesnt scale to arbitrary uploads.

## What I did / decided
annotate people as exclude-person so model detects them and SKIPS re-encoding — skin/face stay natural. feels backwards until you say it out loud: you label so you can leave them alone. kept it bc we lacked time to redesign annotation.

## What came of it
FastAPI + React. live demo https://acra-sandy.vercel.app

## Source bullets used
- TITLE: messy notes — ACRA (Adaptive Color Re-Encoding)
- problem: signs maps posters with color codes collapse for those viewers. global filters wreck the whole image. redesign doesnt scale to arbitrary uploads.
- what i owned: pipeline re-encoding design + frontend design bits.
- weird decision that stuck: annotate people as exclude-person so model detects them and SKIPS re-encoding — skin/face stay natural. feels backwards until you say it out loud: you label so you can leave them alone. kept it bc we lacked time to redesign annotation.
- stack: FastAPI + React. live demo https://acra-sandy.vercel.app
- repo https://github.com/Zeref538/ACRA (private; co-author)
- pass bars locked in code/pipeline/metrics.py — not vibes:
- ΔE improvement > 15
- conflict resolution > 80%
- naturalness ΔE₀₀ < 12
