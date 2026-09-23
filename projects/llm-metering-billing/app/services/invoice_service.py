from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.tenant import Tenant
from app.services.quota_service import QuotaService
from app.services.meter_service import MeterService
from app.config import settings


class InvoiceService:
    @classmethod
    def generate_statement(cls, db: Session, tenant_id: str) -> Dict[str, Any]:
        """
        Generates an itemized monthly statement / invoice with detailed usage line items.
        Stretch Goal: Invoices (monthly statements with usage line items).
        """
        subscription = QuotaService.get_tenant_subscription(db, tenant_id)
        plan = subscription.plan
        rollup = MeterService.get_usage_rollup(db, tenant_id)

        tokens_breakdown = rollup["tokens"]["breakdown"]
        std_input = tokens_breakdown["standard_input"]
        cached_input = tokens_breakdown["cached_input"]
        std_output = tokens_breakdown["standard_output"]
        reasoning = tokens_breakdown["reasoning"]
        api_calls_count = rollup["api_calls"]["used"]

        line_items: List[Dict[str, Any]] = []

        # 1. Base Subscription Plan line item
        line_items.append({
            "item": f"{plan.name} Monthly Subscription",
            "quantity": 1,
            "unit_price_cents": plan.price_cents,
            "total_cents": plan.price_cents,
            "total_usd": f"${plan.price_cents / 100:.2f}"
        })

        # 2. Standard Input Tokens
        input_micros = (std_input * settings.price_standard_input_per_1m_micros) // 1_000_000
        line_items.append({
            "item": "AI Input Tokens (Standard)",
            "quantity": std_input,
            "unit_rate_per_1m": "$2.50",
            "cost_micros": input_micros,
            "cost_usd": f"${input_micros / 1_000_000:.6f}"
        })

        # 3. Cached Input Tokens
        cached_micros = (cached_input * settings.price_cached_input_per_1m_micros) // 1_000_000
        line_items.append({
            "item": "AI Input Tokens (Cached - 75% Discount)",
            "quantity": cached_input,
            "unit_rate_per_1m": "$0.625",
            "cost_micros": cached_micros,
            "cost_usd": f"${cached_micros / 1_000_000:.6f}"
        })

        # 4. Standard Output Tokens
        output_micros = (std_output * settings.price_output_per_1m_micros) // 1_000_000
        line_items.append({
            "item": "AI Output Tokens (Standard)",
            "quantity": std_output,
            "unit_rate_per_1m": "$10.00",
            "cost_micros": output_micros,
            "cost_usd": f"${output_micros / 1_000_000:.6f}"
        })

        # 5. Reasoning Tokens (Billed as Output)
        reasoning_micros = (reasoning * settings.price_reasoning_per_1m_micros) // 1_000_000
        line_items.append({
            "item": "AI Reasoning / Thinking Tokens (Billed at Output Rate)",
            "quantity": reasoning,
            "unit_rate_per_1m": "$10.00",
            "cost_micros": reasoning_micros,
            "cost_usd": f"${reasoning_micros / 1_000_000:.6f}"
        })

        # 6. Billable API calls base fees
        api_micros = api_calls_count * settings.price_per_api_call_micros
        line_items.append({
            "item": "Billable API Invocations",
            "quantity": api_calls_count,
            "unit_rate_per_call": "$0.0005",
            "cost_micros": api_micros,
            "cost_usd": f"${api_micros / 1_000_000:.6f}"
        })

        total_usage_micros = input_micros + cached_micros + output_micros + reasoning_micros + api_micros
        subscription_cents = plan.price_cents
        subscription_micros = subscription_cents * 10_000
        grand_total_micros = subscription_micros + total_usage_micros
        grand_total_usd = f"${grand_total_micros / 1_000_000:.4f}"

        return {
            "invoice_number": f"INV-{tenant_id.upper()}-{int(datetime.now(timezone.utc).timestamp())}",
            "tenant_id": tenant_id,
            "billing_period": rollup["billing_period"],
            "currency": "USD",
            "plan": plan.name,
            "line_items": line_items,
            "summary": {
                "subscription_cents": subscription_cents,
                "usage_micros": total_usage_micros,
                "grand_total_micros": grand_total_micros,
                "grand_total_usd": grand_total_usd,
            },
            "status": "finalized",
            "issued_at": datetime.now(timezone.utc).isoformat()
        }

