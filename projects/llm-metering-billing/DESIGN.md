# Phase 1 Design Document: Usage Metering & Billing Engine

**Author:** FlyRank Backend Intern  
**Track:** Backend Track Capstone  
**Target Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic, SQLite/PostgreSQL, Stripe Test Mode  

---

## 1. Problem Statement

Every modern SaaS—especially those offering AI-powered capabilities—must solve three core billing problems reliably:
1. **Accurate Metering:** Tracking exact customer resource consumption across regular API calls and multi-tier AI tokens (standard input, cached input, output, and reasoning tokens).
2. **Honest Quota Enforcement:** Protecting system margins by rejecting calls when tenants exceed plan boundaries, communicating exact state via unambiguous HTTP status codes (`429 Too Many Requests` vs `402 Payment Required`).
3. **Double-Count Prevention (Idempotency):** Ensuring network retries, client timeouts, and duplicate Stripe webhook deliveries never record duplicate usage events or overcharge the customer.

Bugs in metering directly translate to lost revenue or customer overcharging. This engine is built to guarantee **exactly-once metering** and **deterministic financial math** under real-world retry conditions.

---

## 2. Explicit Non-Goals

To keep the system bounded, secure, and fully zero-cost:
- **No Real AI Model Execution:** The engine meters simulated token usage; it does not invoke external paid model APIs (OpenAI/Anthropic/Gemini) on the request path.
- **No Live Stripe Mode or Real Credit Cards:** All payments operate strictly in Stripe Test Mode (`sk_test_...` and test card `4242 4242 4242 4242`).
- **No Multi-Currency Tax / VAT Calculations:** All monetary accounting is denominated in USD integer micro-units ($1.00 = 1,000,000 micro-units; 1 cent = 10,000 micro-units) to eliminate floating-point rounding errors.

---

## 3. Data Model & Tenant Isolation

Every billable resource, subscription, and usage event belongs strictly to a single `tenant_id`. Queries isolate tenant data by scoping on `tenant_id`.

```
+--------------------+        +------------------------+        +--------------------+
|      Tenant        | 1    1 |      Subscription      | *    1 |        Plan        |
+--------------------+--------+------------------------+--------+--------------------+
| id (UUID / str) PK |        | id (UUID / str) PK     |        | id (UUID / str) PK |
| name (VARCHAR)     |        | tenant_id (FK) UNIQUE  |        | code ('free','pro')|
| email (VARCHAR)    |        | plan_id (FK)           |        | name (VARCHAR)     |
| stripe_customer_id |        | stripe_subscription_id |        | api_call_limit     |
| created_at (UTC)   |        | status ('active', etc) |        | token_limit        |
+--------------------+        | current_period_start   |        | price_cents        |
         |                    | current_period_end     |        +--------------------+
         | 1                  +------------------------+
         |
         | *
+------------------------------------+        +------------------------------------+
|            UsageEvent              |        |         IdempotencyRecord          |
+------------------------------------+        +------------------------------------+
| id (UUID / str) PK                 |        | id (UUID / str) PK                 |
| tenant_id (FK, INDEX)              |        | tenant_id (FK)                     |
| event_type ('api_call', 'tokens')  |        | key (VARCHAR, UNIQUE with tenant)  |
| input_tokens (INT)                 |        | request_hash (VARCHAR SHA256)      |
| cached_input_tokens (INT)          |        | status ('processing','completed')  |
| output_tokens (INT)                |        | response_code (INT)                |
| reasoning_tokens (INT)             |        | response_body (TEXT / JSON)        |
| cost_micros (BIGINT)               |        | created_at (UTC, INDEX)            |
| idempotency_key (VARCHAR, NULLABLE)|        | expires_at (UTC)                   |
| timestamp (UTC, INDEX)             |        +------------------------------------+
+------------------------------------+

+------------------------------------+
|       ProcessedWebhookEvent        |
+------------------------------------+
| id (UUID / str) PK                 |
| stripe_event_id (VARCHAR, UNIQUE)  |
| event_type (VARCHAR)               |
| processed_at (UTC)                 |
+------------------------------------+
```

### Plans & Quotas Definition
| Plan | Price | Monthly API Call Quota | Monthly AI Token Quota | Overage Allowed |
| :--- | :--- | :--- | :--- | :--- |
| **Free** | \$0 / mo | 1,000 calls | 100,000 tokens | No (Blocked with 429/402) |
| **Pro** | \$29 / mo | 50,000 calls | 10,000,000 tokens | Quota warnings at 80% / 100% |

---

## 4. API Surface Contract

### `POST /generate` (Billable Endpoint)
- **Headers:** `X-Tenant-ID: <tenant_id>`, `Idempotency-Key: <uuid-or-string>` (optional but recommended)
- **Request Body:**
  ```json
  {
    "prompt": "Summarize this document",
    "simulated_usage": {
      "input_tokens": 1200,
      "cached_input_tokens": 400,
      "output_tokens": 300,
      "reasoning_tokens": 150
    }
  }
  ```
- **Responses:**
  - `200 OK`: Request allowed, metered, cost calculated.
    ```json
    {
      "status": "success",
      "data": {
        "output": "Simulated AI completion for tenant...",
        "tokens_billed": {
          "fresh_input": 800,
          "cached_input": 400,
          "standard_output": 300,
          "reasoning_output": 150,
          "total_effective_tokens": 1650
        },
        "cost_micros": 6750,
        "cost_usd": "$0.006750"
      },
      "quota": {
        "api_calls_remaining": 994,
        "tokens_remaining": 92350
      }
    }
    ```
  - `429 Too Many Requests`: Tenant exceeded their plan quota limit during the billing window.
    Headers: `Retry-After: 86400`
    ```json
    {
      "error": "usage_quota_exceeded",
      "message": "Monthly API call limit reached (1000/1000). Upgrade to Pro for 50,000 calls.",
      "plan": "Free",
      "metric": "api_calls",
      "used": 1000,
      "limit": 1000
    }
    ```
  - `402 Payment Required`: Tenant subscription lapsed, canceled, or past-due.
    ```json
    {
      "error": "payment_required",
      "message": "Subscription is inactive or past due. Please update payment method.",
      "plan": "Pro",
      "status": "past_due"
    }
    ```
  - `409 Conflict`: Concurrent request with identical idempotency key currently in-flight.

### `GET /usage` (Rollup Endpoint)
- **Headers:** `X-Tenant-ID: <tenant_id>`
- **Response (`200 OK`):**
  ```json
  {
    "tenant_id": "tenant_free",
    "plan": "Free",
    "billing_period": {
      "start": "2026-09-01T00:00:00Z",
      "end": "2026-10-01T00:00:00Z"
    },
    "api_calls": {
      "used": 542,
      "limit": 1000,
      "percentage": 54.2
    },
    "tokens": {
      "used": 28450,
      "limit": 100000,
      "percentage": 28.45,
      "breakdown": {
        "standard_input": 15000,
        "cached_input": 5000,
        "standard_output": 6000,
        "reasoning": 2450
      }
    },
    "total_cost": {
      "micros": 121375,
      "cents": 12,
      "formatted": "$0.121375"
    }
  }
  ```

### `POST /billing/checkout-session`
- **Headers:** `X-Tenant-ID: <tenant_id>`
- **Request Body:** `{"plan_code": "pro"}`
- **Response (`200 OK`):** `{"checkout_url": "https://checkout.stripe.com/c/pay/cs_test_..."}`

### `POST /webhooks/stripe`
- **Headers:** `Stripe-Signature: t=...,v1=...`
- **Body:** Raw byte payload from Stripe.
- **Verification:** Cryptographic HMAC signature check using `STRIPE_WEBHOOK_SECRET`. Bad signature -> `400 Bad Request`.
- **Deduplication:** Event ID stored in `processed_webhook_events`. Duplicate event -> immediate `200 OK` ("already processed").

---

## 5. Idempotency Strategy

1. **Client Header:** Client supplies `Idempotency-Key: <KEY>`.
2. **Lookup:** Check `idempotency_records` by `(tenant_id, key)`.
   - **Found & `completed`:** Return stored `response_code` and `response_body` with header `X-Idempotent-Replay: true`. No usage event is created.
   - **Found & `processing`:** Return `409 Conflict` (request already in flight).
3. **Atomic Write:** If not found, insert record in `processing` state, check quotas, execute billing deduction, insert `usage_events` record, update idempotency status to `completed`, and commit in a single database transaction.

---

## 6. AI Token Pricing Arithmetic

Pinned constants ($1.00 = 1,000,000 micro-units):
- Standard Input: \$2.50 / 1M = 2.5 micro-units per token.
- Cached Input: \$0.625 / 1M = 0.625 micro-units per token (75% cheaper).
- Standard Output: \$10.00 / 1M = 10.0 micro-units per token.
- Reasoning Output: \$10.00 / 1M = 10.0 micro-units per token (classified as output).
- Base Call: \$0.0005 = 500 micro-units per call.

**Calculation Formula:**
$$\text{Cost} = (\text{fresh\_input} \times 2.5) + (\text{cached\_input} \times 0.625) + ((\text{output} + \text{reasoning}) \times 10.0) + \text{base\_call}$$
All values are computed using integer operations (scaled by 1,000 to keep fractional micro-units exact, then divided at boundary).

---

## 7. Layered Architecture Sketch

```
[ HTTP Layer ]       app/routers/ (generate, usage, billing, webhooks)
      |              - Input validation via Pydantic
      |              - Boundary HTTP exception handling (400, 402, 429)
      v
[ Logic Layer ]      app/services/ (MeterService, QuotaService, PricingEngine, StripeService)
      |              - Idempotency coordination
      |              - Quota verification before action
      |              - Deterministic money math
      v
[ Persistence ]      app/models/ & app/database.py (SQLAlchemy 2.0 + Alembic)
                     - Isolated tenant scopes
                     - ACID transaction boundaries
                     - Migrations & indexes
      ^
      |
[ Background Jobs ]  app/jobs/ (ReconciliationWorker, UsageRollupWorker)
                     - Stripe sync verification
                     - 80% / 100% quota threshold alert logging
```

