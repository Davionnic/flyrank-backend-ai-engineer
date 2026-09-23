# Step 3 — Voice-card punch

**Voice:** direct, plain, blunt, no buzzwords, show the work

## Punched case

**Problem**  
easy to think youre on Postgres when DATABASE_URL is missing and you silently hit SQLite.

**What I did / decided**  
primary deploy: PostgreSQL in Docker via docker compose. SQLite fallback when DATABASE_URL missing.

**What came of it**  
README has curl examples, Dockerfile + docker-compose.yml exist, /docs swagger when running.

## One-liner (for bio / card)
easy to think youre on Postgres when DATABASE_URL is missing and you silently hit SQLite. I primary deploy: PostgreSQL in Docker via docker compose. SQLite fallback when DATABASE_URL missing.. Result: README has curl examples, Dockerfile + docker-compose.yml exist, /docs swagger when running.

## Buzzword scrub
Removed matches for: cutting-edge, seamless, leverage, empower, synergy, robust, next-gen, revolutionary, game-changing, best-in-class, world-class (if present).
