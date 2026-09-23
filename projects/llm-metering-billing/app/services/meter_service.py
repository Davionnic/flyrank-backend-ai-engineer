import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from app.models.idempotency import IdempotencyRecord
from app.models.usage_event import UsageEvent
from app.services.pricing_engine import PricingEngine, TokenUsage, PricingResult
from app.services.quota_service import QuotaService, QuotaStatus


class MeterService:
    @staticmethod
    def compute_request_hash(tenant_id: str, path: str, payload: dict) -> str:
        serialized = json.dumps(payload, sort_keys=True)
        raw = f"{tenant_id}:{path}:{serialized}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @classmethod
    def process_billable_request(
        cls,
        db: Session,
        tenant_id: str,
        path: str,
        payload: dict,
        usage: TokenUsage,
        idempotency_key: Optional[str] = None,
        event_type: str = "generate"
    ) -> Tuple[Dict[str, Any], int, bool]:
        """
        Processes a billable request with idempotency validation,
        quota verification, and integer token cost calculation.
        """
        request_hash = cls.compute_request_hash(tenant_id, path, payload) if idempotency_key else None
        record = None

        if idempotency_key:
            # Query existing idempotency record
            record = (
                db.query(IdempotencyRecord)
                .filter(
                    IdempotencyRecord.tenant_id == tenant_id,
                    IdempotencyRecord.key == idempotency_key
                )
                .first()
            )

            if record:
                # Key already seen - first verify request payload matches
                if record.request_hash != request_hash:
                    raise HTTPException(
                        status_code=422,
                        detail={
                            "error": "idempotency_key_reused",
                            "message": "Idempotency key was previously used with a different request payload."
                        }
                    )

                if record.status == "completed":
                    # Exact match replay: return original response with no duplicate event
                    cached_data = json.loads(record.response_body) if record.response_body else {}
                    return cached_data, record.response_code or 200, True

                if record.status == "processing":
                    raise HTTPException(
                        status_code=409,
                        detail={
                            "error": "conflict",
                            "message": "A request with this Idempotency-Key is currently in progress."
                        }
                    )
            else:
                # Reserve idempotency key in processing state
                record = IdempotencyRecord(
                    tenant_id=tenant_id,
                    key=idempotency_key,
                    request_hash=request_hash,
                    status="processing",
                )
                db.add(record)
                db.flush()

        try:
            # Total requested tokens for quota check
            requested_tokens = (
                usage.input_tokens
                + usage.cached_input_tokens
                + usage.output_tokens
                + usage.reasoning_tokens
            )

            # 2. Check quota boundaries (raises 429 or 402 if exceeded)
            quota_status: QuotaStatus = QuotaService.check_quota(
                db=db,
                tenant_id=tenant_id,
                requested_calls=1,
                requested_tokens=requested_tokens
            )

            pricing: PricingResult = PricingEngine.calculate_cost(usage=usage, include_api_call=True)

            usage_event = UsageEvent(
                tenant_id=tenant_id,
                event_type=event_type,
                input_tokens=usage.input_tokens,
                cached_input_tokens=usage.cached_input_tokens,
                output_tokens=usage.output_tokens,
                reasoning_tokens=usage.reasoning_tokens,
                cost_micros=pricing.total_cost_micros,
                idempotency_key=idempotency_key,
                timestamp=datetime.now(timezone.utc)
            )
            db.add(usage_event)

            response_data = {
                "status": "success",
                "tenant_id": tenant_id,
                "plan": quota_status.plan_code,
                "tokens_billed": {
                    "standard_input": pricing.input_tokens,
                    "cached_input": pricing.cached_input_tokens,
                    "standard_output": pricing.output_tokens,
                    "reasoning_output": pricing.reasoning_tokens,
                    "effective_input_tokens": pricing.effective_input_tokens,
                    "effective_output_tokens": pricing.effective_output_tokens,
                    "total_tokens": pricing.total_tokens,
                },
                "cost": {
                    "micros": pricing.total_cost_micros,
                    "cents": pricing.total_cost_micros // 10_000,
                    "usd": pricing.cost_usd,
                    "breakdown_micros": {
                        "standard_input": pricing.input_cost_micros,
                        "cached_input": pricing.cached_input_cost_micros,
                        "standard_output": pricing.output_cost_micros,
                        "reasoning_output": pricing.reasoning_cost_micros,
                        "api_call": pricing.api_call_cost_micros,
                    }
                },
                "quota": {
                    "api_calls_remaining": quota_status.api_calls_remaining,
                    "tokens_remaining": quota_status.tokens_remaining,
                    "period_end": quota_status.period_end.isoformat(),
                }
            }

            if record:
                record.status = "completed"
                record.response_code = 200
                record.response_body = json.dumps(response_data)

            db.commit()
            return response_data, 200, False

        except Exception as exc:
            db.rollback()
            if record and isinstance(exc, HTTPException) and exc.status_code >= 400:
                # Remove transient record so client can retry with valid parameters if desired
                try:
                    db.query(IdempotencyRecord).filter(
                        IdempotencyRecord.tenant_id == tenant_id,
                        IdempotencyRecord.key == idempotency_key
                    ).delete()
                    db.commit()
                except Exception:
                    pass
            raise exc

    @classmethod
    def get_usage_rollup(cls, db: Session, tenant_id: str) -> Dict[str, Any]:
        """
        Aggregates all usage events for the tenant's current billing cycle.
        Returns: { used, limit, cost }
        """
        subscription = QuotaService.get_tenant_subscription(db, tenant_id)
        plan = subscription.plan

        period_start = subscription.current_period_start
        period_end = subscription.current_period_end

        # Aggregate metrics
        totals = (
            db.query(
                func.count(UsageEvent.id).label("total_calls"),
                func.coalesce(func.sum(UsageEvent.input_tokens), 0).label("sum_input"),
                func.coalesce(func.sum(UsageEvent.cached_input_tokens), 0).label("sum_cached"),
                func.coalesce(func.sum(UsageEvent.output_tokens), 0).label("sum_output"),
                func.coalesce(func.sum(UsageEvent.reasoning_tokens), 0).label("sum_reasoning"),
                func.coalesce(func.sum(UsageEvent.cost_micros), 0).label("sum_cost_micros"),
            )
            .filter(
                UsageEvent.tenant_id == tenant_id,
                UsageEvent.timestamp >= period_start,
                UsageEvent.timestamp <= period_end
            )
            .first()
        )

        total_calls = totals.total_calls if totals else 0
        sum_input = int(totals.sum_input) if totals else 0
        sum_cached = int(totals.sum_cached) if totals else 0
        sum_output = int(totals.sum_output) if totals else 0
        sum_reasoning = int(totals.sum_reasoning) if totals else 0
        sum_cost_micros = int(totals.sum_cost_micros) if totals else 0

        total_tokens = sum_input + sum_cached + sum_output + sum_reasoning

        call_pct = round((total_calls / plan.api_call_limit) * 100, 2) if plan.api_call_limit > 0 else 0.0
        token_pct = round((total_tokens / plan.token_limit) * 100, 2) if plan.token_limit > 0 else 0.0

        dollars = sum_cost_micros // 1_000_000
        fractional_micros = sum_cost_micros % 1_000_000
        cost_usd = f"${dollars}.{fractional_micros:06d}"

        return {
            "tenant_id": tenant_id,
            "plan": {
                "code": plan.code,
                "name": plan.name,
                "status": subscription.status,
            },
            "billing_period": {
                "start": period_start.isoformat(),
                "end": period_end.isoformat(),
            },
            "api_calls": {
                "used": total_calls,
                "limit": plan.api_call_limit,
                "remaining": max(0, plan.api_call_limit - total_calls),
                "percentage_used": min(100.0, call_pct),
            },
            "tokens": {
                "used": total_tokens,
                "limit": plan.token_limit,
                "remaining": max(0, plan.token_limit - total_tokens),
                "percentage_used": min(100.0, token_pct),
                "breakdown": {
                    "standard_input": sum_input,
                    "cached_input": sum_cached,
                    "standard_output": sum_output,
                    "reasoning": sum_reasoning,
                }
            },
            "cost": {
                "total_micros": sum_cost_micros,
                "total_cents": sum_cost_micros // 10_000,
                "formatted_usd": cost_usd,
            }
        }
