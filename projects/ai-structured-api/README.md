# BE-07 — Connect to an AI API (structured extract)

FastAPI endpoint that sends text to an LLM (or deterministic mock) and returns **validated structured JSON**.

Monorepo path: `projects/ai-structured-api/` inside
[flyrank-backend-ai-engineer](https://github.com/Davionnic/flyrank-backend-ai-engineer).

## What you get

- `POST /v1/extract` → `{ summary, tags[], sentiment, confidence }` (Pydantic-validated)
- Timeout + retries on the real OpenAI-compatible HTTP path (`httpx` + `tenacity`)
- Cost / token logging (JSONL + structured log lines)
- Kill switch: `LLM_ENABLED=false` → **503**
- Mock provider behind the same interface when `MOCK_LLM=1` (no API key needed)

No secrets in the repo. Copy `.env.example` → `.env` if you want a real key.

## Eval score (real run)

```
fixtures=8
schema_valid=8/8 (100.0%)
soft_match=8/8 (100.0%)
SCORE=100.0
```

Re-run: `MOCK_LLM=1 python eval/run_eval.py`  
Artifact: [`docs/eval-results.json`](docs/eval-results.json)

## Run

```bash
cd projects/ai-structured-api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Default: mock (deterministic, free, offline)
export MOCK_LLM=1
export LLM_ENABLED=true
uvicorn main:app --reload --port 8007
```

Real LLM (optional): set `MOCK_LLM=0`, `OPENAI_API_KEY=...`, optionally `OPENAI_BASE_URL` / `OPENAI_MODEL`.

## Curl

```bash
# Health
curl -s http://localhost:8007/health

# Extract
curl -s -X POST http://localhost:8007/v1/extract \
  -H 'content-type: application/json' \
  -d '{"text":"The new product update is excellent. Customers love the great performance and quality."}'
```

Example response (mock):

```json
{
  "result": {
    "summary": "The new product update is excellent.",
    "tags": ["product", "customer", "quality", "performance", "update"],
    "sentiment": "positive",
    "confidence": 0.84
  },
  "provider": "mock",
  "model": "mock-deterministic-v1",
  "usage": {
    "prompt_tokens": 88,
    "completion_tokens": 38,
    "total_tokens": 126,
    "cost_usd": 0.0
  }
}
```

```bash
# Validation — whitespace-only text
curl -i -X POST http://localhost:8007/v1/extract \
  -H 'content-type: application/json' \
  -d '{"text":"   "}'
# → 422

# Kill switch
LLM_ENABLED=false uvicorn main:app --port 8008
curl -i -X POST http://localhost:8008/v1/extract \
  -H 'content-type: application/json' \
  -d '{"text":"hello"}'
# → 503 {"detail":"LLM calls disabled (LLM_ENABLED=false / kill switch)"}
```

Full local transcript: [`docs/curl-proof.txt`](docs/curl-proof.txt)

## Design notes

| Piece | How |
|-------|-----|
| Schema | `ExtractResult` in `schemas.py` — summary, tags, sentiment, confidence |
| Provider | `provider.py` — `MockProvider` + `OpenAICompatibleProvider` |
| Retries | `tenacity` on timeout / transport / 5xx / 429; timeout via `LLM_TIMEOUT_SECONDS` |
| Cost | `cost.py` appends JSONL to `COST_LOG_PATH` (default `logs/cost.jsonl`) |
| Kill switch | `LLM_ENABLED=false` checked before any provider call |

Mock was used for the curl proof and eval on this box — no `OPENAI_*` / `ANTHROPIC` / `GROQ` / `GEMINI` keys in the environment. The OpenAI-compatible client path is still implemented and switches on when `MOCK_LLM=0` + key present.

## Layout

```
projects/ai-structured-api/
  main.py           # FastAPI app
  schemas.py        # Pydantic models
  provider.py       # mock + OpenAI-compatible
  cost.py           # usage / cost JSONL
  settings.py       # env config
  eval/             # fixtures + scorer
  docs/             # curl proof + eval results
  .env.example
```
