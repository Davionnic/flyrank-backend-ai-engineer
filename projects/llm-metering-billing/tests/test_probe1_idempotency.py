from app.models.usage_event import UsageEvent
from app.models.idempotency import IdempotencyRecord


def test_probe_1_idempotent_metering_duplicate_prevention(client, db_session):
    """Retrying with the same idempotency key should record exactly one event and replay the original response."""
    tenant_id = "tenant_free"
    idempotency_key = "test-idem-key-probe-1"
    headers = {
        "X-Tenant-ID": tenant_id,
        "Idempotency-Key": idempotency_key,
    }
    payload = {
        "prompt": "Test AI request for idempotency probe",
        "simulated_usage": {
            "input_tokens": 100,
            "cached_input_tokens": 50,
            "output_tokens": 80,
            "reasoning_tokens": 20
        }
    }

    # Verify initial state: 0 events for this tenant
    initial_events_count = db_session.query(UsageEvent).filter(UsageEvent.tenant_id == tenant_id).count()
    assert initial_events_count == 0

    # 1. Send first request
    res1 = client.post("/generate", json=payload, headers=headers)
    assert res1.status_code == 200, res1.text
    data1 = res1.json()

    # Verify 1 usage event recorded
    events_after_first = db_session.query(UsageEvent).filter(UsageEvent.tenant_id == tenant_id).all()
    assert len(events_after_first) == 1
    assert events_after_first[0].idempotency_key == idempotency_key
    assert "X-Idempotent-Replay" not in res1.headers

    # 2. Send EXACT same request a second time with the same idempotency key (simulating retry)
    res2 = client.post("/generate", json=payload, headers=headers)
    assert res2.status_code == 200, res2.text
    data2 = res2.json()

    # Verify EXACTLY one usage event remains in database (NO double count!)
    events_after_second = db_session.query(UsageEvent).filter(UsageEvent.tenant_id == tenant_id).all()
    assert len(events_after_second) == 1, f"Expected 1 usage event, found {len(events_after_second)}"

    # Verify response body mirrors original response
    assert data1 == data2
    # Verify replay header is present on second response
    assert res2.headers.get("X-Idempotent-Replay") == "true"

    # Verify idempotency record state
    record = db_session.query(IdempotencyRecord).filter(
        IdempotencyRecord.tenant_id == tenant_id,
        IdempotencyRecord.key == idempotency_key
    ).first()
    assert record is not None
    assert record.status == "completed"
    assert record.response_code == 200

