import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session
import stripe
from app.config import settings
from app.models.tenant import Tenant
from app.models.subscription import Subscription
from app.models.plan import Plan
from app.services.quota_service import QuotaService

logger = logging.getLogger("reconciliation_service")
stripe.api_key = settings.stripe_secret_key


class ReconciliationService:
    @classmethod
    def check_usage_alerts(cls, db: Session) -> List[Dict[str, Any]]:
        """
        Inspects all tenants to detect quota threshold crossings (80% and 100%).
        Generates structured alerts for warning and quota exhaustion.
        """
        alerts = []
        tenants = db.query(Tenant).all()

        for tenant in tenants:
            subscription = db.query(Subscription).filter(Subscription.tenant_id == tenant.id).first()
            if not subscription or subscription.status != "active":
                continue

            plan = subscription.plan
            calls_used, tokens_used = QuotaService.get_current_period_usage(
                db, tenant.id, subscription.current_period_start
            )

            call_pct = (calls_used / plan.api_call_limit) * 100 if plan.api_call_limit > 0 else 0
            token_pct = (tokens_used / plan.token_limit) * 100 if plan.token_limit > 0 else 0

            max_pct = max(call_pct, token_pct)

            if max_pct >= 100.0:
                alert = {
                    "tenant_id": tenant.id,
                    "level": "CRITICAL",
                    "metric": "calls" if call_pct >= 100.0 else "tokens",
                    "percentage": round(max_pct, 1),
                    "message": f"Tenant '{tenant.id}' has reached 100% of {plan.name} quota.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                alerts.append(alert)
                logger.warning(f"[QUOTA ALERT CRITICAL] {alert['message']}")

            elif max_pct >= 80.0:
                alert = {
                    "tenant_id": tenant.id,
                    "level": "WARNING",
                    "metric": "calls" if call_pct >= 80.0 else "tokens",
                    "percentage": round(max_pct, 1),
                    "message": f"Tenant '{tenant.id}' reached {round(max_pct, 1)}% of {plan.name} quota. Upgrade recommended.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                alerts.append(alert)
                logger.info(f"[QUOTA ALERT WARNING] {alert['message']}")

        return alerts

    @classmethod
    def reconcile_stripe_subscriptions(cls, db: Session, max_retries: int = 3) -> Dict[str, Any]:
        """
        Audits local subscription database against Stripe API (source of truth).
        Detects missed webhooks and updates drifted status.
        Includes retry logic with failure alerts.
        """
        if not settings.stripe_secret_key or settings.stripe_secret_key.startswith("sk_test_placeholder"):
            logger.info("Stripe key is in placeholder/mock mode. Skipping remote Stripe API calls.")
            return {
                "status": "skipped",
                "reason": "mock_mode",
                "audited": 0,
                "reconciled": 0
            }

        subscriptions = db.query(Subscription).filter(Subscription.stripe_subscription_id.isnot(None)).all()
        audited_count = 0
        reconciled_count = 0
        drift_items = []

        for sub in subscriptions:
            audited_count += 1
            remote_sub = None

            # Retry loop with exponential backoff
            for attempt in range(1, max_retries + 1):
                try:
                    remote_sub = stripe.Subscription.retrieve(sub.stripe_subscription_id)
                    break
                except stripe.error.StripeError as err:
                    if attempt == max_retries:
                        logger.error(
                            f"[RECONCILIATION FAILURE ALERT] Failed retrieving Stripe sub '{sub.stripe_subscription_id}' after {max_retries} attempts: {err}"
                        )
                    else:
                        time.sleep(0.5 * attempt)

            if remote_sub:
                remote_status = remote_sub.status
                if sub.status != remote_status:
                    logger.warning(
                        f"[DRIFT DETECTED] Subscription '{sub.id}' local status '{sub.status}' != Stripe status '{remote_status}'. Syncing."
                    )
                    sub.status = remote_status
                    reconciled_count += 1
                    drift_items.append({
                        "subscription_id": sub.id,
                        "old_status": sub.status,
                        "new_status": remote_status
                    })

        db.commit()
        return {
            "status": "success",
            "audited": audited_count,
            "reconciled": reconciled_count,
            "drift_items": drift_items
        }

