import json
from tests.utils import generate_stripe_signature_header


def test_probe_3_stripe_checkout_and_webhook_flips_free_to_pro(client):
    """Test that processing a valid checkout.session.completed webhook upgrades tenant to Pro and updates limits."""
    tenant_id = "tenant_free"

    # 1. Before webhook: Tenant is on Free plan
    res_before = client.get("/usage", headers={"X-Tenant-ID": tenant_id})
    assert res_before.status_code == 200
    usage_before = res_before.json()
    assert usage_before["plan"]["code"] == "free"
    assert usage_before["api_calls"]["limit"] == 1000
    assert usage_before["tokens"]["limit"] == 100000

    # 2. Initiate Checkout Session
    checkout_res = client.post(
        "/billing/checkout-session",
        json={"plan_code": "pro"},
        headers={"X-Tenant-ID": tenant_id}
    )
    assert checkout_res.status_code == 200
    checkout_data = checkout_res.json()
    assert "checkout_url" in checkout_data

    # 3. Simulate Stripe test webhook for checkout.session.completed
    event_payload = {
        "id": "evt_test_checkout_probe_3",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_session_12345",
                "client_reference_id": tenant_id,
                "customer": "cus_test_stripe_customer_789",
                "subscription": "sub_test_stripe_subscription_999",
                "metadata": {
                    "tenant_id": tenant_id,
                    "plan_code": "pro"
                }
            }
        }
    }
    payload_bytes = json.dumps(event_payload).encode("utf-8")
    sig_header = generate_stripe_signature_header(payload_bytes)

    webhook_res = client.post(
        "/webhooks/stripe",
        content=payload_bytes,
        headers={"Stripe-Signature": sig_header, "Content-Type": "application/json"}
    )
    assert webhook_res.status_code == 200, webhook_res.text
    webhook_data = webhook_res.json()
    assert webhook_data["status"] == "success"
    assert "upgraded to plan 'pro'" in webhook_data["message"]

    # 4. GET /usage now shows the new Pro limits!
    res_after = client.get("/usage", headers={"X-Tenant-ID": tenant_id})
    assert res_after.status_code == 200
    usage_after = res_after.json()

    assert usage_after["plan"]["code"] == "pro"
    assert usage_after["api_calls"]["limit"] == 50000
    assert usage_after["tokens"]["limit"] == 10000000

