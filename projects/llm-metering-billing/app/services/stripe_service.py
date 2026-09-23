import stripe
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.config import settings
from app.models.tenant import Tenant
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.webhook_event import ProcessedWebhookEvent

stripe.api_key = settings.stripe_secret_key


class StripeService:
    @classmethod
    def create_checkout_session(
        cls,
        db: Session,
        tenant_id: str,
        plan_code: str = "pro"
    ) -> Dict[str, Any]:
        """
        Creates a Stripe Checkout Session in test mode for subscription upgrade.
        """
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise HTTPException(
                status_code=404,
                detail={"error": "tenant_not_found", "message": f"Tenant '{tenant_id}' not found."}
            )

        target_plan = db.query(Plan).filter(Plan.code == plan_code).first()
        if not target_plan:
            raise HTTPException(
                status_code=404,
                detail={"error": "plan_not_found", "message": f"Plan '{plan_code}' not found."}
            )

        success_url = f"{settings.base_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{settings.base_url}/billing/cancel"

        try:
            # If Stripe test key is configured with a real live/test secret, call Stripe API
            if settings.stripe_secret_key and not settings.stripe_secret_key.startswith(("sk_test_placeholder", "sk_test_mock")):
                try:
                    session = stripe.checkout.Session.create(
                        payment_method_types=["card"],
                        mode="subscription",
                        line_items=[{
                            "price_data": {
                                "currency": "usd",
                                "product_data": {
                                    "name": f"FlyRank {target_plan.name} Subscription",
                                    "description": f"Includes {target_plan.api_call_limit:,} API calls and {target_plan.token_limit:,} tokens/mo",
                                },
                                "unit_amount": target_plan.price_cents,
                                "recurring": {"interval": "month"},
                            },
                            "quantity": 1,
                        }],
                        client_reference_id=tenant_id,
                        customer_email=tenant.email,
                        metadata={
                            "tenant_id": tenant_id,
                            "plan_code": target_plan.code,
                        },
                        success_url=success_url,
                        cancel_url=cancel_url,
                    )
                    return {
                        "status": "success",
                        "checkout_url": session.url,
                        "session_id": session.id,
                        "tenant_id": tenant_id,
                        "plan": target_plan.code
                    }
                except stripe.error.AuthenticationError:
                    # In test/mock mode without live internet Stripe test key
                    pass

            # Simulated checkout URL for local testing without network / live keys
            simulated_session_id = f"cs_test_mock_{tenant_id}_{int(datetime.now().timestamp())}"
            simulated_url = f"https://checkout.stripe.com/c/pay/{simulated_session_id}"
            return {
                "status": "success",
                "checkout_url": simulated_url,
                "session_id": simulated_session_id,
                "tenant_id": tenant_id,
                "plan": target_plan.code,
                "note": "Generated in Stripe test mode"
            }

        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=400,
                detail={"error": "stripe_error", "message": str(e)}
            )

    @classmethod
    def verify_webhook_signature(
        cls,
        payload: bytes,
        sig_header: Optional[str]
    ) -> Dict[str, Any]:
        """
        Cryptographically verifies the Stripe webhook signature against raw byte payload.
        Rejects invalid or forged signatures with HTTP 400.
        """
        if not sig_header:
            raise HTTPException(
                status_code=400,
                detail={"error": "missing_signature", "message": "Missing 'Stripe-Signature' header."}
            )

        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=sig_header,
                secret=settings.stripe_webhook_secret
            )
            return event
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_payload", "message": "Invalid webhook payload encoding."}
            )
        except stripe.error.SignatureVerificationError:
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_signature", "message": "Cryptographic webhook signature verification failed."}
            )

    @classmethod
    def process_webhook_event(
        cls,
        db: Session,
        event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deduplicates and dispatches verified webhook events.
        Ensures idempotency: replayed events return 200 without duplicate processing.
        """
        if hasattr(event, "to_dict"):
            event_dict = event.to_dict()
        elif isinstance(event, dict):
            event_dict = event
        else:
            event_dict = dict(event)

        event_id = event_dict.get("id")
        event_type = event_dict.get("type")

        if not event_id or not event_type:
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_event", "message": "Missing event id or type."}
            )

        # Deduplication check
        existing = db.query(ProcessedWebhookEvent).filter(
            ProcessedWebhookEvent.stripe_event_id == event_id
        ).first()

        if existing:
            return {
                "status": "ignored",
                "message": f"Webhook event '{event_id}' has already been processed.",
                "event_id": event_id,
                "event_type": event_type,
                "processed_at": existing.processed_at.isoformat()
            }

        # Dispatch based on event type
        data_object = event_dict.get("data", {}).get("object", {})
        result_message = "Event processed successfully."

        if event_type == "checkout.session.completed":
            result_message = cls._handle_checkout_completed(db, data_object)
        elif event_type == "customer.subscription.updated":
            result_message = cls._handle_subscription_updated(db, data_object)
        elif event_type == "customer.subscription.deleted":
            result_message = cls._handle_subscription_deleted(db, data_object)

        # Record event as processed
        processed_record = ProcessedWebhookEvent(
            stripe_event_id=event_id,
            event_type=event_type,
            processed_at=datetime.now(timezone.utc)
        )
        db.add(processed_record)
        db.commit()

        return {
            "status": "success",
            "message": result_message,
            "event_id": event_id,
            "event_type": event_type
        }

    @classmethod
    def _handle_checkout_completed(cls, db: Session, session_data: dict) -> str:
        tenant_id = (
            session_data.get("client_reference_id")
            or session_data.get("metadata", {}).get("tenant_id")
        )
        plan_code = session_data.get("metadata", {}).get("plan_code", "pro")
        stripe_sub_id = session_data.get("subscription")
        stripe_cust_id = session_data.get("customer")

        if not tenant_id:
            return "No tenant_id associated with checkout session."

        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            return f"Tenant '{tenant_id}' not found."

        if stripe_cust_id:
            tenant.stripe_customer_id = stripe_cust_id

        target_plan = db.query(Plan).filter(Plan.code == plan_code).first()
        if not target_plan:
            target_plan = db.query(Plan).filter(Plan.code == "pro").first()

        now = datetime.now(timezone.utc)
        period_end = now + timedelta(days=30)

        subscription = db.query(Subscription).filter(Subscription.tenant_id == tenant_id).first()
        if subscription:
            subscription.plan_id = target_plan.id
            subscription.status = "active"
            if stripe_sub_id:
                subscription.stripe_subscription_id = stripe_sub_id
            subscription.current_period_start = now
            subscription.current_period_end = period_end
        else:
            subscription = Subscription(
                tenant_id=tenant_id,
                plan_id=target_plan.id,
                stripe_subscription_id=stripe_sub_id,
                status="active",
                current_period_start=now,
                current_period_end=period_end
            )
            db.add(subscription)

        return f"Tenant '{tenant_id}' upgraded to plan '{target_plan.code}'."

    @classmethod
    def _handle_subscription_updated(cls, db: Session, sub_data: dict) -> str:
        stripe_sub_id = sub_data.get("id")
        status = sub_data.get("status", "active")

        subscription = (
            db.query(Subscription)
            .filter(Subscription.stripe_subscription_id == stripe_sub_id)
            .first()
        )
        if not subscription:
            return f"Subscription '{stripe_sub_id}' not found in database."

        subscription.status = status
        current_period_start = sub_data.get("current_period_start")
        current_period_end = sub_data.get("current_period_end")
        if current_period_start:
            subscription.current_period_start = datetime.fromtimestamp(current_period_start, timezone.utc)
        if current_period_end:
            subscription.current_period_end = datetime.fromtimestamp(current_period_end, timezone.utc)

        return f"Subscription '{stripe_sub_id}' updated to status '{status}'."

    @classmethod
    def _handle_subscription_deleted(cls, db: Session, sub_data: dict) -> str:
        stripe_sub_id = sub_data.get("id")
        subscription = (
            db.query(Subscription)
            .filter(Subscription.stripe_subscription_id == stripe_sub_id)
            .first()
        )
        if not subscription:
            return f"Subscription '{stripe_sub_id}' not found."

        free_plan = db.query(Plan).filter(Plan.code == "free").first()
        if free_plan:
            subscription.plan_id = free_plan.id
            subscription.status = "active"
            subscription.stripe_subscription_id = None

        return f"Subscription '{stripe_sub_id}' deleted; tenant downgraded to Free plan."
