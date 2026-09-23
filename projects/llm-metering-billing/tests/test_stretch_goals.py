from datetime import datetime, timezone, timedelta
from app.services.proration_service import ProrationService
from app.services.reconciliation_service import ReconciliationService


def test_stretch_invoice_generation_with_itemized_breakdown(client):
    """
    Test Stretch Goal: Invoices (monthly statements with itemized usage line items).
    """
    tenant_id = "tenant_pro"
    # Meter a request with token breakdown
    payload = {
        "prompt": "Document analysis invoice test",
        "simulated_usage": {
            "input_tokens": 1000,
            "cached_input_tokens": 200,
            "output_tokens": 500,
            "reasoning_tokens": 100
        }
    }
    headers = {"X-Tenant-ID": tenant_id}
    client.post("/generate", json=payload, headers=headers)

    # Fetch itemized invoice
    res = client.get("/billing/invoice", headers=headers)
    assert res.status_code == 200
    inv = res.json()

    assert inv["tenant_id"] == tenant_id
    assert inv["status"] == "finalized"
    assert len(inv["line_items"]) == 6

    # Verify line items include subscription and token categories
    item_names = [li["item"] for li in inv["line_items"]]
    assert any("Monthly Subscription" in name for name in item_names)
    assert any("Input Tokens (Standard)" in name for name in item_names)
    assert any("Input Tokens (Cached" in name for name in item_names)
    assert any("Output Tokens (Standard)" in name for name in item_names)
    assert any("Reasoning / Thinking Tokens" in name for name in item_names)
    assert any("Billable API Invocations" in name for name in item_names)


def test_stretch_mid_cycle_proration_math():
    """
    Test Stretch Goal: Exact integer proration calculation for mid-cycle plan upgrades.
    """
    now = datetime.now(timezone.utc)
    period_start = now - timedelta(days=15)
    period_end = now + timedelta(days=15)  # 30 day cycle, upgrade at day 15 (50% elapsed)

    current_price_cents = 0       # Free plan
    target_price_cents = 2900     # Pro plan ($29.00)

    result = ProrationService.calculate_mid_cycle_proration(
        period_start=period_start,
        period_end=period_end,
        upgrade_time=now,
        current_price_cents=current_price_cents,
        target_price_cents=target_price_cents,
        current_plan_code="free",
        target_plan_code="pro"
    )

    # Remaining is half of the cycle -> exactly 50% of $29.00 = $14.50 (1450 cents)
    assert result.net_charge_cents == 1450
    assert result.net_charge_usd == "$14.50"


def test_stretch_reconciliation_and_usage_alerts(db_session):
    """
    Test Stretch Goal: Quota threshold inspection (80% / 100% alerts).
    """
    alerts = ReconciliationService.check_usage_alerts(db_session)
    # tenant_boundary is at 999/1000 calls (99.9%), should trigger a WARNING alert
    assert len(alerts) >= 1
    boundary_alert = next((a for a in alerts if a["tenant_id"] == "tenant_boundary"), None)
    assert boundary_alert is not None
    assert boundary_alert["level"] == "WARNING"
    assert boundary_alert["percentage"] == 99.9

