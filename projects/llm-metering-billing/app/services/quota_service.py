from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from app.models.tenant import Tenant
from app.models.subscription import Subscription
from app.models.plan import Plan
from app.models.usage_event import UsageEvent
from app.config import settings
from dataclasses import dataclass


@dataclass
class QuotaStatus:
    allowed: bool
    plan_code: str
    plan_name: str
    api_calls_used: int
    api_calls_limit: int
    api_calls_remaining: int
    tokens_used: int
    tokens_limit: int
    tokens_remaining: int
    period_start: datetime
    period_end: datetime


class QuotaService:
    @staticmethod
    def get_tenant_subscription(db: Session, tenant_id: str) -> Subscription:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise HTTPException(
                status_code=404,
                detail={"error": "tenant_not_found", "message": f"Tenant '{tenant_id}' does not exist."}
            )

        subscription = (
            db.query(Subscription)
            .filter(Subscription.tenant_id == tenant_id)
            .first()
        )
        if not subscription:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "payment_required",
                    "message": "No active subscription found for tenant. Upgrade to Free or Pro to begin.",
                }
            )

        # Check subscription status
        if subscription.status in ["past_due", "unpaid", "canceled"]:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "payment_required",
                    "message": f"Subscription is {subscription.status}. Payment or renewal required to continue usage.",
                    "status": subscription.status,
                    "plan": subscription.plan.code
                }
            )

        return subscription

    @staticmethod
    def get_current_period_usage(db: Session, tenant_id: str, period_start: datetime):
        # Aggregate API calls count and token sum since period_start
        stats = (
            db.query(
                func.count(UsageEvent.id).label("call_count"),
                func.coalesce(
                    func.sum(
                        UsageEvent.input_tokens
                        + UsageEvent.cached_input_tokens
                        + UsageEvent.output_tokens
                        + UsageEvent.reasoning_tokens
                    ),
                    0
                ).label("total_tokens")
            )
            .filter(
                UsageEvent.tenant_id == tenant_id,
                UsageEvent.timestamp >= period_start
            )
            .first()
        )
        calls_used = stats.call_count if stats else 0
        tokens_used = int(stats.total_tokens) if stats else 0
        return calls_used, tokens_used

    @classmethod
    def check_quota(
        cls,
        db: Session,
        tenant_id: str,
        requested_calls: int = 1,
        requested_tokens: int = 0
    ) -> QuotaStatus:
        subscription = cls.get_tenant_subscription(db, tenant_id)
        plan = subscription.plan

        period_start = subscription.current_period_start
        if period_start.tzinfo is None:
            period_start = period_start.replace(tzinfo=timezone.utc)

        period_end = subscription.current_period_end
        if period_end.tzinfo is None:
            period_end = period_end.replace(tzinfo=timezone.utc)

        calls_used, tokens_used = cls.get_current_period_usage(
            db, tenant_id, period_start
        )

        now = datetime.now(timezone.utc)
        retry_after_seconds = max(1, int((period_end - now).total_seconds()))

        # Check API calls limit
        if calls_used + requested_calls > plan.api_call_limit:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "usage_quota_exceeded",
                    "message": (
                        f"Monthly API call quota exceeded. {calls_used}/{plan.api_call_limit} calls used. "
                        f"Next call exceeds quota. Upgrade to Pro for {settings.pro_plan_api_limit:,} calls/month."
                    ),
                    "metric": "api_calls",
                    "used": calls_used,
                    "limit": plan.api_call_limit,
                    "plan": plan.code
                },
                headers={"Retry-After": str(retry_after_seconds)}
            )

        # Check Token limit
        if tokens_used + requested_tokens > plan.token_limit:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "usage_quota_exceeded",
                    "message": (
                        f"Monthly AI token quota exceeded. {tokens_used}/{plan.token_limit} tokens used. "
                        f"Requested {requested_tokens} tokens exceeds remaining limit. Upgrade to Pro for more tokens."
                    ),
                    "metric": "ai_tokens",
                    "used": tokens_used,
                    "limit": plan.token_limit,
                    "plan": plan.code
                },
                headers={"Retry-After": str(retry_after_seconds)}
            )

        return QuotaStatus(
            allowed=True,
            plan_code=plan.code,
            plan_name=plan.name,
            api_calls_used=calls_used,
            api_calls_limit=plan.api_call_limit,
            api_calls_remaining=plan.api_call_limit - calls_used - requested_calls,
            tokens_used=tokens_used,
            tokens_limit=plan.token_limit,
            tokens_remaining=plan.token_limit - tokens_used - requested_tokens,
            period_start=subscription.current_period_start,
            period_end=subscription.current_period_end,
        )
