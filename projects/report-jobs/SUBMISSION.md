# BE-06 Submission — Your first background job

## Monorepo GitHub URL

https://github.com/Davionnic/flyrank-backend-ai-engineer/tree/main/projects/report-jobs

## Stack

- FastAPI on `:8000`
- Inngest Python SDK (`is_production=False`, `INNGEST_DEV=1`)
- Inngest Dev Server (`npx inngest-cli@latest dev -u http://localhost:8000/api/inngest`) on `:8288`

## Curl proof summary (local box, 2026-09-23 21:41 CST)

| Check | Result |
|-------|--------|
| `GET /health` | **200** `{"status":"ok"}` |
| `POST /reports` `{"topic":"cats"}` | **202** in **11ms** → `{id, status:"pending"}` |
| Immediate `GET /reports/{id}` | **pending** |
| Poll ~10s later | **done** + result (`headline`, `summary`, `bullets`) |
| `POST /reports` `{"topic":""}` | **400** `topic is required` (no event enqueued) |
| `POST /reports` `{}` | **400** |
| `POST /reports` `{"topic":"fail"}` | **202**, then store **failed**; Inngest **3 attempts** (retries=2) then **FAILED** |
| Unknown id | **404** |

Full transcript: [`docs/curl-proof.txt`](docs/curl-proof.txt)  
Fail-run GraphQL history (attempts 0/1/2): [`docs/inngest-fail-run-history.json`](docs/inngest-fail-run-history.json)  
Runs list: [`docs/inngest-runs.json`](docs/inngest-runs.json)

## Stage 3 — why validation must not retry

Empty/missing `topic` is a **client input error**. Enqueueing would waste workers; retries would fail the same way forever. Return **400** at the HTTP edge and **do not** send `report/requested`. Retries belong on transient worker failures (`topic: "fail"` → `"The report oven is broken!"`).

## Stage 4 — cron answers

| Wanted schedule | Cron |
|-----------------|------|
| Every day at 08:00 | `0 8 * * *` |
| Sunday 22:00 | `0 22 * * 0` |

Heartbeat in this project: `* * * * *` (every minute) — logs pending/done/failed counts (observed in uvicorn logs during proof).

## Dashboard screenshot

Not attached — computerUse/browser screenshot not available in this executor. Evidence instead: curl transcript + Inngest GraphQL history showing `make-report` steps (`think` sleep + `build-report`) and **three attempts** on fail ending `FunctionFailed`.

## Fix applied during local proof

Inngest Python SDK **0.5.x** handlers take a single `ctx: inngest.Context` (use `ctx.step`); int sleep is milliseconds — use `timedelta(seconds=…)` for the 5s/8s sleeps. Old `(ctx, step)` signature caused HTTP 500 from `/api/inngest`.
