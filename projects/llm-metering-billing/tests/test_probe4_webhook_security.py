import json
from app.models.webhook_event import ProcessedWebhookEvent
from tests.utils import generate_stripe_signature_header


def test_probe_4_forged_webhook_signature_rejected_400(client, db_session):
    """Forged or invalid signatures must be rejected with 400 Bad Request."""
    event_payload = {
        "id": "evt_forged_probe_4",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {"object": {"client_reference_id": "tenant_free"}}
    }
    payload_bytes = json.dumps(event_payload).encode("utf-8")

    # Send with forged signature
    res = client.post(
        "/webhooks/stripe",
        content=payload_bytes,
        headers={"Stripe-Signature": "t=1700000000,v1=invalid_forged_signature_hex"}
    )
    assert res.status_code == 400, f"Expected 400 for forged signature, got {res.status_code}"
    data = res.json()
    assert data["error"] == "invalid_signature"

    # Verify event was NOT recorded in database
    existing = db_session.query(ProcessedWebhookEvent).filter(
        ProcessedWebhookEvent.stripe_event_id == "evt_forged_probe_4"
    ).first()
    assert existing is None


def test_probe_4_replay_real_event_twice_processed_once(client, db_session):
    """Replaying a processed webhook should return 200 without duplicate execution."""
    event_id = "evt_replay_test_probe_4"
    event_payload = {
        "id": event_id,
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_session_replay",
                "client_reference_id": "tenant_free",
                "metadata": {"tenant_id": "tenant_free", "plan_code": "pro"}
            }
        }
    }
    payload_bytes = json.dumps(event_payload).encode("utf-8")
    valid_sig = generate_stripe_signature_header(payload_bytes)

    # 1. First delivery of webhook
    res1 = client.post(
        "/webhooks/stripe",
        content=payload_bytes,
        headers={"Stripe-Signature": valid_sig}
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] == "success"

    # 2. Second delivery (replay attack or network duplicate)
    res2 = client.post(
        "/webhooks/stripe",
        content=payload_bytes,
        headers={"Stripe-Signature": valid_sig}
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["status"] == "ignored"
    assert "already been processed" in data2["message"]

    # Verify database has exactly 1 processed record for this event
    records = db_session.query(ProcessedWebhookEvent).filter(
        ProcessedWebhookEvent.stripe_event_id == event_id
    ).all()
    assert len(records) == 1

