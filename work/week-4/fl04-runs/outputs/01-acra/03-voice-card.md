# Step 3 — Voice-card punch

**Voice:** direct, plain, blunt, no buzzwords, show the work

## Punched case

**Problem**  
signs maps posters with color codes collapse for those viewers. global filters wreck the whole image. redesign doesnt scale to arbitrary uploads.

**What I did / decided**  
annotate people as exclude-person so model detects them and SKIPS re-encoding — skin/face stay natural. feels backwards until you say it out loud: you label so you can leave them alone. kept it bc we lacked time to redesign annotation.

**What came of it**  
FastAPI + React. live demo https://acra-sandy.vercel.app

## One-liner (for bio / card)
signs maps posters with color codes collapse for those viewers. I annotate people as exclude-person so model detects them and SKIPS re-encoding — skin/face stay natural. feels backwards until you say it out loud: you label so you can leave them alone. kept it bc we lacked time to redesign annotation.. Result: FastAPI + React. live demo https://acra-sandy.ver

## Buzzword scrub
Removed matches for: cutting-edge, seamless, leverage, empower, synergy, robust, next-gen, revolutionary, game-changing, best-in-class, world-class (if present).
