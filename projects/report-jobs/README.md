# BE-06 — Your first background job

FastAPI + **Inngest** report API for FlyRank Backend.

Monorepo path: `projects/report-jobs/` inside
[flyrank-backend-ai-engineer](https://github.com/Davionnic/flyrank-backend-ai-engineer).

## What it does

- `POST /reports` returns **202 + id** immediately (fast door).
- Inngest function `make-report` sleeps ~8s, then writes the result.
- `GET /reports/{id}` goes `pending` → `done` (or `failed`).
- Topic `fail` retries twice (3 attempts total) then Failed.
- Cron `heartbeat` every minute logs pending/done/failed counts.

## Run (two processes)

```bash
cd projects/report-jobs
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Terminal A — API on :8000
uvicorn main:app --reload --port 8000

# Terminal B — Inngest Dev Server (discovers /api/inngest)
npx inngest-cli@latest dev -u http://localhost:8000/api/inngest
```

Dashboard: http://localhost:8288

## Endpoints / functions

| Kind | Name | Notes |
|------|------|--------|
| GET | `/health` | `{ "status": "ok" }` |
| POST | `/reports` | body `{ "topic": "cats" }` → **202** `{ id, status }` |
| GET | `/reports/{id}` | pending / done+result / failed / **404** |
| Inngest | `say-hello` | event `test/hello`, sleep 5s |
| Inngest | `make-report` | event `report/requested`, sleep 8s, retries=2 |
| Inngest | `heartbeat` | cron `* * * * *` |

## Curl proof

```bash
# Fast door (<1s → 202)
curl -i -X POST http://localhost:8000/reports \
  -H 'content-type: application/json' \
  -d '{"topic":"cats"}'
# HTTP/1.1 202 Accepted
# {"id":"<uuid>","status":"pending"}

# Poll while pending
curl -s http://localhost:8000/reports/<uuid>
# {"id":"...","topic":"cats","status":"pending"}

# After ~8s (with Inngest Dev Server running)
curl -s http://localhost:8000/reports/<uuid>
# {"id":"...","topic":"cats","status":"done","result":{...}}

# Validation — no event sent
curl -i -X POST http://localhost:8000/reports \
  -H 'content-type: application/json' \
  -d '{"topic":""}'
# HTTP/1.1 400

# Fail + retries (watch dashboard for 3 attempts)
curl -s -X POST http://localhost:8000/reports \
  -H 'content-type: application/json' \
  -d '{"topic":"fail"}'
```

## Stage 3 — why validation must not retry

A missing/empty `topic` is a **client input error**. Enqueueing a job would waste workers; retries would fail the same way forever. Return **400** at the HTTP edge and **do not** send `report/requested`.

Retries belong on **transient worker failures** (topic `fail` → `"The report oven is broken!"` with `retries: 2` → 3 attempts then Failed in the dashboard).

## Stage 4 — cron answers

| Wanted schedule | Cron |
|-----------------|------|
| Every day at 08:00 | `0 8 * * *` |
| Sunday 22:00 | `0 22 * * 0` (Sunday; `7` also means Sunday on some crons) |

Heartbeat here uses `* * * * *` (every minute) and logs store counts.

## Stages (commits)

0. Hello `/health` server  
1. Inngest `say-hello`  
2. Fast door + `make-report`  
3. Retries + 400 validation  
4. Cron heartbeat  
5. Publish README (this file)

## Dashboard screenshot

Run the Dev Server, trigger a report and a `fail` topic, then screenshot http://localhost:8288 showing `make-report` steps (sleep + run) and three attempts on fail. Save as `docs/inngest-dashboard.png` if attaching evidence.
