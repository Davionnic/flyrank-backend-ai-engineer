def test_missing_tenant_id_header(client):
    res = client.post("/generate", json={"prompt": "hello"})
    assert res.status_code == 400
    assert res.json()["error"] == "missing_header"


def test_nonexistent_tenant_returns_404(client):
    res = client.post(
        "/generate",
        json={"prompt": "hello"},
        headers={"X-Tenant-ID": "non_existent_tenant_999"}
    )
    assert res.status_code == 404
    assert res.json()["error"] == "tenant_not_found"


def test_negative_tokens_rejected_with_422(client):
    res = client.post(
        "/generate",
        json={
            "prompt": "hello",
            "simulated_usage": {"input_tokens": -50}
        },
        headers={"X-Tenant-ID": "tenant_free"}
    )
    assert res.status_code == 422
    data = res.json()
    assert data["error"] == "validation_error"


def test_empty_prompt_rejected_with_422(client):
    res = client.post(
        "/generate",
        json={"prompt": ""},
        headers={"X-Tenant-ID": "tenant_free"}
    )
    assert res.status_code == 422
    assert res.json()["error"] == "validation_error"


def test_idempotency_key_payload_mismatch_rejected(client):
    key = "idem-reuse-test-key"
    headers = {"X-Tenant-ID": "tenant_free", "Idempotency-Key": key}

    # First request
    res1 = client.post("/generate", json={"prompt": "Payload 1"}, headers=headers)
    assert res1.status_code == 200

    # Second request with SAME key but DIFFERENT payload
    res2 = client.post("/generate", json={"prompt": "Payload 2 DIFFERENT"}, headers=headers)
    assert res2.status_code == 422
    assert res2.json()["error"] == "idempotency_key_reused"

