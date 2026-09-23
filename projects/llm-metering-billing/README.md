# Usage Metering & Billing Engine

Backend service for SaaS usage metering, quota enforcement, and Stripe subscription sync. Built with FastAPI, SQLAlchemy, and SQLite/PostgreSQL.

---

## Architecture

```
Client Request
      │
      ├── POST /generate ────> [ Idempotency Check ]
      │                              │
      │                              ├── Key exists & completed -> Return cached response (X-Idempotent-Replay)
      │                              └── Fresh key -> Reserve key
      │                                       │
      │                                       v
      │                              [ Quota Enforcement ]
      │                                       │
      │                                       ├── Over limit -> 429 Too Many Requests
      │                                       ├── Past due/unpaid -> 402 Payment Required
      │                                       └── Allowed -> Calculate token pricing
      │                                                          │
      │                                                          v
      │                                                    [ Store Event ]
      │                                                    - Save usage_event
      │                                                    - Update idempotency record
      │
      ├── GET /usage ────────> [ Usage Rollup ]
      │                            - Aggregate calls & token breakdown for billing period
      │                            - Return used, limit, remaining, and integer cost
      │
      ├── POST /billing/checkout-session -> Initiate Stripe Checkout (test mode)
      │
      └── POST /webhooks/stripe ───> [ Webhook Handler ]
                                          - Cryptographic HMAC signature verification
                                          - Event deduplication (ProcessedWebhookEvent)
                                          - Synchronize tenant plan (Free <-> Pro)
```

---

## Setup & Running

### Requirements
- Python 3.11+

### 1. Install Dependencies
```bash
pip install -r requirements.txt
cp .env.example .env
```

### 2. Seed Database
Seeds default Free/Pro plans and test tenants:
```bash
python -m app.seed
```

Demo tenants created:
- `tenant_free`: Free plan (1,000 calls / 100k tokens limit)
- `tenant_pro`: Pro plan (50,000 calls / 10M tokens limit)
- `tenant_boundary`: Free plan pre-loaded at 999/1,000 calls to test quota boundary behavior
- `tenant_unpaid`: Pro plan with status `past_due` to test 402 responses

### 3. Start the Server
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
API docs available at `http://localhost:8000/docs`.

### 4. Run Tests
```bash
python -m pytest -v
```

### 5. Background Reconciliation Worker
Runs Stripe subscription sync and checks for tenants near or at quota (80% / 100%):
```bash
python -m app.worker
```

### Optional: Docker Run
```bash
docker compose up --build
```

---

## API Endpoints

| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/generate` | Billable action endpoint. Supports `X-Tenant-ID` and `Idempotency-Key` headers. |
| `GET` | `/usage` | Monthly usage rollup, quota percentages, and cost breakdown. |
| `POST` | `/billing/checkout-session` | Creates Stripe Checkout session for plan upgrade. |
| `POST` | `/webhooks/stripe` | Stripe webhook endpoint. Signature-verified and deduplicated. |
| `GET` | `/billing/invoice` | Itemized statement with usage line items. |
| `GET` | `/billing/proration-preview` | Mid-cycle upgrade proration calculation. |
| `GET` | `/health` | Health check. |

---

## Core Implementation Details

### Idempotency
- Requests accept an optional `Idempotency-Key` header.
- The service tracks `(tenant_id, key)` pairs alongside a SHA-256 hash of the request payload.
- Retrying with the same key returns the cached response with `X-Idempotent-Replay: true` without recording additional usage.
- Reusing an existing key with a mutated payload returns `422 Unprocessable Entity`.

### Quota Enforcement
- Enforced before recording usage.
- Calls up to the exact limit succeed (`200 OK`). The first call exceeding the limit fails with `429 Too Many Requests` and includes a `Retry-After` header.
- Tenants with canceled or past-due subscriptions receive `402 Payment Required`.

### Money & Token Math
- All monetary amounts are handled and stored as integer micro-units (`1 USD = 1,000,000 micros`, `1 cent = 10,000 micros`) to avoid floating point inaccuracies.
- Pricing constants pinned in `app/config.py`:
  - Standard input: \$2.50 / 1M tokens (2.5 micros / token)
  - Cached input: \$0.625 / 1M tokens (0.625 micros / token, 75% discount)
  - Output tokens: \$10.00 / 1M tokens (10.0 micros / token)
  - Reasoning tokens: \$10.00 / 1M tokens (billed at output rate)
  - Base call charge: \$0.0005 per call (500 micros)

### Stripe Webhook Verification & Deduplication
- Raw request bytes are verified using Stripe HMAC-SHA256 (`stripe.Webhook.construct_event`).
- Invalid signatures return `400 Bad Request`.
- Handled events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`.
- Processed event IDs are stored in `processed_webhook_events`. Duplicate deliveries return `200 OK` without re-applying state changes.

---

## Limitations

- Token counts in `/generate` are simulated for metering and cost calculation; no external LLM API is called.
- Stripe integration runs in test mode only (`sk_test_...`).
- Single-currency accounting in USD; no multi-currency FX or tax handling.
