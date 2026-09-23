# messy notes — task-crud-api (BE-01..04)

FlyRank backend track. FastAPI CRUD for tasks.
primary deploy: PostgreSQL in Docker via docker compose. SQLite fallback when DATABASE_URL missing.
path in monorepo: projects/task-crud-api/

endpoints i care about for a case writeup:
GET /health (shows db type)
GET/POST /tasks, GET/PUT/DELETE /tasks/{id}
filter ?done= and ?search=
GET /stats, POST /reset to seed

problem: easy to think youre on Postgres when DATABASE_URL is missing and you silently hit SQLite.
pain points from building:
- env: DATABASE_URL for postgres vs silent sqlite — easy to think youre on postgres when youre not
- docker compose one-command is the story; local pip path is fallback
- ownership: this is my internship service work inside Davionnic/flyrank-backend-ai-engineer, not a separate product company

proof: README has curl examples, Dockerfile + docker-compose.yml exist, /docs swagger when running.
dont claim production traffic or SLA. claim: containerized CRUD API with health that reports which DB you hit.

CTA later: email gallodave.cs@gmail.com about junior backend role.
