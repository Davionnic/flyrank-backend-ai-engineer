# BE-07 Submission — Connect to an AI API

## Monorepo GitHub URL

https://github.com/Davionnic/flyrank-backend-ai-engineer/tree/main/projects/ai-structured-api

## Stack

- FastAPI (`POST /v1/extract`, `GET /health`)
- Pydantic v2 schema validation
- OpenAI-compatible HTTP client (`httpx`) + deterministic mock behind the same interface
- Retries / timeout via `tenacity` + `LLM_TIMEOUT_SECONDS`
- Cost JSONL logging (`logs/cost.jsonl`)
- Kill switch `LLM_ENABLED=false` → 503

## Provider used for proof

**Mock** (`MOCK_LLM=1`). Box had no `OPENAI_API_KEY` / Anthropic / Groq / Gemini env vars. Real HTTP client path is present; set `MOCK_LLM=0` + key to use it.

## Curl proof summary (local box, 2026-09-23 21:51 CST)

| Check | Result |
|-------|--------|
| `GET /health` | **200** `llm_enabled=true`, `mock_llm=true` |
| `POST /v1/extract` happy path | **200** validated `{summary,tags,sentiment,confidence}` |
| Whitespace / missing text | **422** |
| `LLM_ENABLED=false` | **503** kill switch |
| Cost log | JSONL line written under `logs/cost.jsonl` |

Transcript: [`docs/curl-proof.txt`](docs/curl-proof.txt)

## Eval score

**SCORE=100.0** (schema 8/8, soft match 8/8) — [`docs/eval-results.json`](docs/eval-results.json)

```bash
MOCK_LLM=1 python eval/run_eval.py
```

## Runnable curl

```bash
cd projects/ai-structured-api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
MOCK_LLM=1 LLM_ENABLED=true uvicorn main:app --port 8007

curl -s -X POST http://localhost:8007/v1/extract \
  -H 'content-type: application/json' \
  -d '{"text":"The new product update is excellent. Customers love the great performance and quality."}'
```
