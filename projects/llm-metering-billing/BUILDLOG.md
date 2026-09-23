# Build Log & AI Usage Notes

Dev journal for the Usage Metering & Billing Engine project.

---

## AI Collaboration Summary

I used an LLM assistant during development mainly for:
- Initial scaffolding of the FastAPI routing and SQLAlchemy models.
- Drafting initial migration scripts and Pydantic schemas.
- Writing test fixtures and generating edge case permutations.

While AI sped up the boilerplate writing, several critical bugs and subtle edge cases required manual debugging and architectural fixes.

---

## Bugs Hit & How They Were Fixed

### 1. Python Module Shadowing in Test Fixtures
When setting up `tests/conftest.py`, the AI wrote:
```python
from app.main import app
import app.models
```
Because `import app.models` runs after `from app.main import app`, the identifier `app` got overwritten by the `app/` package module itself. This caused `app.dependency_overrides[get_db] = ...` to crash with `AttributeError: module 'app' has no attribute 'dependency_overrides'`.
**Fix:** Renamed the import to `from app.main import app as fastapi_app` and explicitly imported the model classes.

### 2. In-Memory SQLite Connections Dropping Tables
Tests initially failed with `sqlite3.OperationalError: no such table: idempotency_records`.
The AI configured `sqlite:///:memory:` but didn't use `StaticPool`. In SQLite, each new connection opened by SQLAlchemy or the FastAPI TestClient connects to a fresh, empty in-memory database.
**Fix:** Added `poolclass=StaticPool` and `connect_args={"check_same_thread": False}` so all test requests share the exact same in-memory SQLite database across threads.

### 3. Timezone Naive vs Aware Datetime Math
When calculating the `Retry-After` header during quota rejection, the code did:
```python
retry_after_seconds = int((subscription.current_period_end - now).total_seconds())
```
This threw `TypeError: can't subtract offset-naive and offset-aware datetimes`. SQLite stores timestamps as plain strings without timezone offsets, so SQLAlchemy loads them back as naive datetimes, while `datetime.now(timezone.utc)` is offset-aware.
**Fix:** Added normalization before doing any timedelta math:
```python
if period_end.tzinfo is None:
    period_end = period_end.replace(tzinfo=timezone.utc)
```

### 4. Stripe SDK v15 `Event` Object Representation
In `app/services/stripe_service.py`, the webhook dispatcher called `event.get("id")` and `event.get("type")`.
In stripe-python v15+, `construct_event` returns a `stripe.Event` object rather than a standard Python `dict`. Trying to call `.get()` raised an `AttributeError`.
**Fix:** Added a check using `hasattr(event, "to_dict")` to convert the Stripe event into a standard dictionary before accessing keys.

### 5. Idempotency Key Mutation Ordering
During testing of idempotency key tampering, sending the same key with a different request body was unexpectedly returning `200 OK` with the cached response instead of failing.
Looking at `meter_service.py`, the code checked `if record.status == "completed": return cached_response` *before* checking `if record.request_hash != request_hash`.
**Fix:** Moved the payload hash comparison to the very top of the key lookup:
```python
if record.request_hash != request_hash:
    raise HTTPException(status_code=422, detail={"error": "idempotency_key_reused", ...})
```
Now, any client that tries to reuse an existing key for a different prompt or payload immediately gets rejected with a `422`.

---

## Key Decisions

1. **Integer Money Storage:** Storing dollar amounts as floats in databases is asking for rounding issues. Everything here uses micro-units (`1 USD = 1,000,000 micros`) so calculations remain exact.
2. **Pre-check Quota Enforcement:** Quotas are checked before processing the request, not after. At boundary (999 -> 1000), call 1000 goes through, and call 1001 gets stopped with a 429.
3. **Webhook Deduplication:** Stripe webhooks can be retried by their servers. Storing processed Stripe event IDs in `processed_webhook_events` ensures we don't accidentally update subscriptions multiple times on duplicate deliveries.
