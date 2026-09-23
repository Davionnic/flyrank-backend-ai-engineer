"""
Probe Demonstration Script for EVIDENCE.md
Executes and prints exact output for all 5 acceptance probes against the live server.
"""
import httpx
import json
import time
from tests.utils import generate_stripe_signature_header

BASE_URL = "http://127.0.0.1:8000"


def run_probes():
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)

    print("================================================================================")
    print("PROBE 1: Send billable request twice with same Idempotency-Key")
    print("================================================================================")
    headers_1 = {
        "X-Tenant-ID": "tenant_free",
        "Idempotency-Key": f"demo-idem-key-{int(time.time())}"
    }
    payload_1 = {
        "prompt": "Summarize this technical article",
        "simulated_usage": {
            "input_tokens": 200,
            "cached_input_tokens": 100,
            "output_tokens": 80,
            "reasoning_tokens": 20
        }
    }
    print(f">> Request 1: POST /generate (Idempotency-Key: {headers_1['Idempotency-Key']})")
    r1 = client.post("/generate", json=payload_1, headers=headers_1)
    print(f"Status Code: {r1.status_code}")
    print(f"Headers: X-Idempotent-Replay = {r1.headers.get('X-Idempotent-Replay')}")
    print(f"Body:\n{json.dumps(r1.json(), indent=2)}\n")

    print(f">> Request 2: POST /generate (RETRY with SAME Idempotency-Key)")
    r2 = client.post("/generate", json=payload_1, headers=headers_1)
    print(f"Status Code: {r2.status_code}")
    print(f"Headers: X-Idempotent-Replay = {r2.headers.get('X-Idempotent-Replay')}")
    print(f"Body:\n{json.dumps(r2.json(), indent=2)}\n")

    print("================================================================================")
    print("PROBE 2: Quota Boundary Honesty (Call #1000 allowed, Call #1001 returns 429)")
    print("================================================================================")
    headers_2 = {"X-Tenant-ID": "tenant_boundary"}
    payload_2 = {
        "prompt": "Boundary quota test call",
        "simulated_usage": {"input_tokens": 10, "output_tokens": 10}
    }
    print(">> Call #1000 (At exact boundary: 1000/1000):")
    r_boundary_1000 = client.post("/generate", json=payload_2, headers=headers_2)
    print(f"Status Code: {r_boundary_1000.status_code}")
    print(f"Body:\n{json.dumps(r_boundary_1000.json(), indent=2)}\n")

    print(">> Call #1001 (Beyond quota: 1001/1000):")
    r_boundary_1001 = client.post("/generate", json=payload_2, headers=headers_2)
    print(f"Status Code: {r_boundary_1001.status_code}")
    print(f"Headers: Retry-After = {r_boundary_1001.headers.get('Retry-After')}")
    print(f"Body:\n{json.dumps(r_boundary_1001.json(), indent=2)}\n")

    print(">> Call with Inactive/Past-Due Subscription (tenant_unpaid):")
    r_unpaid = client.post("/generate", json=payload_2, headers={"X-Tenant-ID": "tenant_unpaid"})
    print(f"Status Code: {r_unpaid.status_code}")
    print(f"Body:\n{json.dumps(r_unpaid.json(), indent=2)}\n")

    print("================================================================================")
    print("PROBE 3: Stripe Checkout & Webhook flips Free -> Pro; GET /usage reflects change")
    print("================================================================================")
    tenant_3 = "tenant_free"
    print(f">> Initial Plan Limits for '{tenant_3}':")
    u1 = client.get("/usage", headers={"X-Tenant-ID": tenant_3}).json()
    print(f"Plan: {u1['plan']['name']}, Call Limit: {u1['api_calls']['limit']}, Token Limit: {u1['tokens']['limit']}")

    print("\n>> Initiating Checkout Session:")
    checkout_res = client.post("/billing/checkout-session", json={"plan_code": "pro"}, headers={"X-Tenant-ID": tenant_3})
    print(f"Checkout Response: {checkout_res.json()}")

    print("\n>> Delivering verified checkout.session.completed Stripe webhook...")
    event_3 = {
        "id": f"evt_demo_checkout_{int(time.time())}",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_session_live_demo",
                "client_reference_id": tenant_3,
                "metadata": {"tenant_id": tenant_3, "plan_code": "pro"}
            }
        }
    }
    raw_body_3 = json.dumps(event_3).encode("utf-8")
    sig_3 = generate_stripe_signature_header(raw_body_3)
    wh_res = client.post("/webhooks/stripe", content=raw_body_3, headers={"Stripe-Signature": sig_3})
    print(f"Webhook Status: {wh_res.status_code}, Body: {wh_res.json()}")

    print(f"\n>> GET /usage after webhook processing:")
    u2 = client.get("/usage", headers={"X-Tenant-ID": tenant_3}).json()
    print(f"Plan: {u2['plan']['name']}, Call Limit: {u2['api_calls']['limit']}, Token Limit: {u2['tokens']['limit']}\n")

    print("================================================================================")
    print("PROBE 4: Webhook Security (Bad Signature -> 400; Replay Event -> Deduplicated)")
    print("================================================================================")
    print(">> Sending forged webhook signature:")
    bad_wh = client.post(
        "/webhooks/stripe",
        content=raw_body_3,
        headers={"Stripe-Signature": "t=1700000000,v1=forged_bad_signature_hex"}
    )
    print(f"Status Code: {bad_wh.status_code}, Body: {bad_wh.json()}")

    print("\n>> Replaying previously processed webhook event:")
    replay_wh = client.post(
        "/webhooks/stripe",
        content=raw_body_3,
        headers={"Stripe-Signature": sig_3}
    )
    print(f"Status Code: {replay_wh.status_code}, Body: {replay_wh.json()}\n")

    print("================================================================================")
    print("PROBE 5: AI Token Pricing Constants & Rollup Verification")
    print("================================================================================")
    tenant_5 = "tenant_pro"
    usage_payload = {
        "prompt": "Complex physics analysis with reasoning",
        "simulated_usage": {
            "input_tokens": 10000,
            "cached_input_tokens": 4000,
            "output_tokens": 2000,
            "reasoning_tokens": 1000
        }
    }
    r5 = client.post("/generate", json=usage_payload, headers={"X-Tenant-ID": tenant_5})
    print(f"Generation Cost: {r5.json()['cost']}")

    u5 = client.get("/usage", headers={"X-Tenant-ID": tenant_5})
    print(f"GET /usage rollup:\n{json.dumps(u5.json(), indent=2)}")


if __name__ == "__main__":
    run_probes()

