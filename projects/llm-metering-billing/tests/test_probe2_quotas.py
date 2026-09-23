from app.models.usage_event import UsageEvent


def test_probe_2_boundary_honesty_and_quota_enforcement(client, db_session):
    """Verify call 1000 succeeds and call 1001 returns 429 with Retry-After header."""
    tenant_id = "tenant_boundary"
    # Pre-seeded count is 999
    initial_count = db_session.query(UsageEvent).filter(UsageEvent.tenant_id == tenant_id).count()
    assert initial_count == 999

    payload = {
        "prompt": "Boundary test request",
        "simulated_usage": {"input_tokens": 10, "output_tokens": 10}
    }
    headers = {"X-Tenant-ID": tenant_id}

    # 1. Exactly at boundary (Call #1000 of 1000): MUST SUCCEED (200 OK)
    res_1000 = client.post("/generate", json=payload, headers=headers)
    assert res_1000.status_code == 200, f"Expected 200 at boundary, got {res_1000.status_code}: {res_1000.text}"
    body_1000 = res_1000.json()
    assert body_1000["status"] == "success"
    assert body_1000["quota"]["api_calls_remaining"] == 0

    count_after_1000 = db_session.query(UsageEvent).filter(UsageEvent.tenant_id == tenant_id).count()
    assert count_after_1000 == 1000

    # 2. Beyond boundary (Call #1001 of 1000): MUST BE REJECTED (429 Too Many Requests)
    res_1001 = client.post("/generate", json=payload, headers=headers)
    assert res_1001.status_code == 429, f"Expected 429 after boundary, got {res_1001.status_code}: {res_1001.text}"
    body_1001 = res_1001.json()

    # Check clear message and structured error response
    assert body_1001["error"] == "usage_quota_exceeded"
    assert "Monthly API call quota exceeded" in body_1001["message"]
    assert body_1001["used"] == 1000
    assert body_1001["limit"] == 1000
    assert "Retry-After" in res_1001.headers

    # Verify no 1001st event was created in the database
    count_after_1001 = db_session.query(UsageEvent).filter(UsageEvent.tenant_id == tenant_id).count()
    assert count_after_1001 == 1000


def test_probe_2_payment_required_on_lapsed_subscription(client):
    """
    Verify 402 Payment Required status code when subscription is past_due / canceled.
    """
    tenant_id = "tenant_unpaid"
    payload = {
        "prompt": "Test unpaid request",
        "simulated_usage": {"input_tokens": 10, "output_tokens": 10}
    }
    headers = {"X-Tenant-ID": tenant_id}

    res = client.post("/generate", json=payload, headers=headers)
    assert res.status_code == 402, f"Expected 402 for lapsed subscription, got {res.status_code}"
    data = res.json()
    assert data["error"] == "payment_required"
    assert "past_due" in data["message"]

