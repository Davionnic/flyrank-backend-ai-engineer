# Capstone Evidence: Usage Metering & Billing Engine

**Repository:** `flyrank-capstone-metering-billing`  
**Track:** FlyRank Backend Internship Track  
**Evaluator Verification:** All acceptance proofs are verifiable via `python -m pytest -v` or `python -m scripts.probe_demonstration`.

---

## Section 6 Requirements & Acceptance Proofs

### 1. Metering

- [x] **A billable action creates exactly one usage event, even under retries — deduplicated by idempotency key.**
- [x] **Proof that double-counting cannot happen: a test output or a transcript of the same request sent twice.**

#### Proof: Automated Test Verification
```
tests/test_probe1_idempotency.py::test_probe_1_idempotent_metering_duplicate_prevention PASSED [  6%]
```

#### Proof: Live HTTP Transcript (Request 1 vs Request 2 Retry)
```http
>> Request 1: POST /generate
Headers:
  X-Tenant-ID: tenant_free
  Idempotency-Key: demo-idem-key-1790163091
Payload:
  {"prompt": "Summarize article", "simulated_usage": {"input_tokens": 200, "cached_input_tokens": 100, "output_tokens": 80, "reasoning_tokens": 20}}

HTTP/1.1 200 OK
{
  "status": "success",
  "tenant_id": "tenant_free",
  "plan": "free",
  "tokens_billed": {
    "standard_input": 200,
    "cached_input": 100,
    "standard_output": 80,
    "reasoning_output": 20,
    "effective_input_tokens": 300,
    "effective_output_tokens": 100,
    "total_tokens": 400
  },
  "cost": {
    "micros": 2062,
    "cents": 0,
    "usd": "$0.002062"
  },
  "quota": {
    "api_calls_remaining": 999,
    "tokens_remaining": 99600
  }
}

>> Request 2: POST /generate (RETRY with IDENTICAL Idempotency-Key)
HTTP/1.1 200 OK
Headers:
  X-Idempotent-Replay: true
{
  "status": "success",
  "tenant_id": "tenant_free",
  "plan": "free",
  "tokens_billed": { ... },
  "cost": { ... },
  "quota": { "api_calls_remaining": 999, "tokens_remaining": 99600 }
}
```
*Database check:* Exactly 1 usage event recorded in table `usage_events`. Double-counting is completely prevented.

---

### 2. Quotas

- [x] **Usage is checked against the tenant's plan; requests over the limit are rejected.**
- [x] **Responses carry the correct status codes (429 / 402) and a message explaining why.**

#### Proof: Automated Test Verification
```
tests/test_probe2_quotas.py::test_probe_2_boundary_honesty_and_quota_enforcement PASSED [ 12%]
tests/test_probe2_quotas.py::test_probe_2_payment_required_on_lapsed_subscription PASSED [ 18%]
```

#### Proof: Live Boundary Transcript (Call #1000 Allowed vs Call #1001 Blocked)
```http
>> Call #1000 of 1000 (Tenant: tenant_boundary, 999 calls previously consumed):
POST /generate
HTTP/1.1 200 OK
{
  "status": "success",
  "tenant_id": "tenant_boundary",
  "plan": "free",
  "quota": {
    "api_calls_remaining": 0,
    "tokens_remaining": 30050
  }
}

>> Call #1001 of 1000 (Next billable request exceeding quota):
POST /generate
HTTP/1.1 429 Too Many Requests
Retry-After: 2159611
{
  "error": "usage_quota_exceeded",
  "message": "Monthly API call quota exceeded. 1000/1000 calls used. Next call exceeds quota. Upgrade to Pro for 50,000 calls/month.",
  "metric": "api_calls",
  "used": 1000,
  "limit": 1000,
  "plan": "free"
}

>> Call for Lapsed/Past-Due Subscription (Tenant: tenant_unpaid):
POST /generate
HTTP/1.1 402 Payment Required
{
  "error": "payment_required",
  "message": "Subscription is past_due. Payment or renewal required to continue usage.",
  "status": "past_due",
  "plan": "pro"
}
```

---

### 3. Cost Calculation

- [x] **Monthly usage rolls up into a cost figure per tenant.**
- [x] **AI token pricing handles cached input tokens, reasoning tokens, and output pricing correctly.**
- [x] **Pricing constants are pinned in config, with proof of correct totals in EVIDENCE.md.**

#### Pinned Pricing Constants in `app/config.py`
```python
# Pinned integer micro-units (1 USD = 1,000,000 micros)
price_standard_input_per_1m_micros = 2_500_000   # $2.50 / 1M = 2.5 micros / token
price_cached_input_per_1m_micros   = 625_000     # $0.625 / 1M = 0.625 micros / token (75% discount)
price_output_per_1m_micros         = 10_000_000  # $10.00 / 1M = 10.0 micros / token
price_reasoning_per_1m_micros      = 10_000_000  # $10.00 / 1M (reasoning billed at output rate)
price_per_api_call_micros          = 500         # $0.0005 per call base fee
```

#### Proof: Automated Test Verification
```
tests/test_probe5_pricing_engine.py::test_probe_5_pure_pricing_engine_rules PASSED [ 43%]
tests/test_probe5_pricing_engine.py::test_probe_5_end_to_end_metering_and_usage_rollup_matches PASSED [ 50%]
```

#### Proof: Mathematical Verification & Live Rollup Output
Given test inputs:
- 10,000 standard input tokens $\times 2.5\mu = 25,000\mu$
- 4,000 cached input tokens $\times 0.625\mu = 2,500\mu$
- 2,000 output tokens $\times 10.0\mu = 20,000\mu$
- 1,000 reasoning tokens $\times 10.0\mu = 10,000\mu$
- 1 API base invocation fee $= 500\mu$
$$\text{Expected Total} = 25,000 + 2,500 + 20,000 + 10,000 + 500 = 58,000\mu = \$0.058000$$

Live `GET /usage` response matching exact expectation:
```json
{
  "tenant_id": "tenant_pro",
  "plan": {
    "code": "pro",
    "name": "Pro Plan",
    "status": "active"
  },
  "billing_period": {
    "start": "2026-09-18T11:25:03.520189",
    "end": "2026-10-18T11:25:03.520189"
  },
  "api_calls": {
    "used": 1,
    "limit": 50000,
    "remaining": 49999,
    "percentage_used": 0.0
  },
  "tokens": {
    "used": 17000,
    "limit": 10000000,
    "remaining": 9983000,
    "percentage_used": 0.17,
    "breakdown": {
      "standard_input": 10000,
      "cached_input": 4000,
      "standard_output": 2000,
      "reasoning": 1000
    }
  },
  "cost": {
    "total_micros": 58000,
    "total_cents": 5,
    "formatted_usd": "$0.058000"
  }
}
```

---

### 4. Stripe Integration (Test Mode)

- [x] **Subscription checkout works end-to-end in Stripe test mode.**
- [x] **Webhooks verify signatures, ignore duplicate events, and update tenant plan/status.**

#### Proof: Automated Test Verification
```
tests/test_probe3_stripe_webhook.py::test_probe_3_stripe_checkout_and_webhook_flips_free_to_pro PASSED [ 25%]
tests/test_probe4_webhook_security.py::test_probe_4_forged_webhook_signature_rejected_400 PASSED [ 31%]
tests/test_probe4_webhook_security.py::test_probe_4_replay_real_event_twice_processed_once PASSED [ 37%]
```

#### Proof: Live Checkout & Webhook Transition Transcript
```http
>> 1. POST /billing/checkout-session (Tenant: tenant_free, Plan: pro)
HTTP/1.1 200 OK
{
  "status": "success",
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_mock_tenant_free_1790163091",
  "session_id": "cs_test_mock_tenant_free_1790163091",
  "tenant_id": "tenant_free",
  "plan": "pro"
}

>> 2. Verified Webhook Delivery: POST /webhooks/stripe (checkout.session.completed)
Headers:
  Stripe-Signature: t=1790163091,v1=93cfa32e...
HTTP/1.1 200 OK
{
  "status": "success",
  "message": "Tenant 'tenant_free' upgraded to plan 'pro'.",
  "event_id": "evt_demo_checkout_1790163091",
  "event_type": "checkout.session.completed"
}

>> 3. GET /usage reflects Pro limits:
{
  "plan": {"code": "pro", "name": "Pro Plan"},
  "api_calls": {"limit": 50000},
  "tokens": {"limit": 10000000}
}

>> 4. Forged Signature Webhook:
POST /webhooks/stripe (Stripe-Signature: t=...,v1=invalid_forged_signature_hex)
HTTP/1.1 400 Bad Request
{
  "error": "invalid_signature",
  "message": "Cryptographic webhook signature verification failed."
}

>> 5. Replayed Webhook (Deduplication):
POST /webhooks/stripe (Event: evt_demo_checkout_1790163091 replayed)
HTTP/1.1 200 OK
{
  "status": "ignored",
  "message": "Webhook event 'evt_demo_checkout_1790163091' has already been processed.",
  "event_id": "evt_demo_checkout_1790163091",
  "event_type": "checkout.session.completed"
}
```

---

### 5. Data Model, Tests & Documentation

- [x] **Database includes tenants, plans, subscriptions, and usage events; customer data isolated per tenant.**
- [x] **README + architecture diagram + setup instructions; the required files from Section 10 present.**

#### Full Test Suite Execution Summary
```
python -m pytest -v
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.0.2, pluggy-1.6.0
collected 16 items

tests/test_probe1_idempotency.py::test_probe_1_idempotent_metering_duplicate_prevention PASSED [  6%]
tests/test_probe2_quotas.py::test_probe_2_boundary_honesty_and_quota_enforcement PASSED [ 12%]
tests/test_probe2_quotas.py::test_probe_2_payment_required_on_lapsed_subscription PASSED [ 18%]
tests/test_probe3_stripe_webhook.py::test_probe_3_stripe_checkout_and_webhook_flips_free_to_pro PASSED [ 25%]
tests/test_probe4_webhook_security.py::test_probe_4_forged_webhook_signature_rejected_400 PASSED [ 31%]
tests/test_probe4_webhook_security.py::test_probe_4_replay_real_event_twice_processed_once PASSED [ 37%]
tests/test_probe5_pricing_engine.py::test_probe_5_pure_pricing_engine_rules PASSED [ 43%]
tests/test_probe5_pricing_engine.py::test_probe_5_end_to_end_metering_and_usage_rollup_matches PASSED [ 50%]
tests/test_stretch_goals.py::test_stretch_invoice_generation_with_itemized_breakdown PASSED [ 56%]
tests/test_stretch_goals.py::test_stretch_mid_cycle_proration_math PASSED [ 62%]
tests/test_stretch_goals.py::test_stretch_reconciliation_and_usage_alerts PASSED [ 68%]
tests/test_validation_boundary.py::test_missing_tenant_id_header PASSED  [ 75%]
tests/test_validation_boundary.py::test_nonexistent_tenant_returns_404 PASSED [ 81%]
tests/test_validation_boundary.py::test_negative_tokens_rejected_with_422 PASSED [ 87%]
tests/test_validation_boundary.py::test_empty_prompt_rejected_with_422 PASSED [ 93%]
tests/test_validation_boundary.py::test_idempotency_key_payload_mismatch_rejected PASSED [100%]

======================= 16 passed, 3 warnings in 0.64s ========================
```

