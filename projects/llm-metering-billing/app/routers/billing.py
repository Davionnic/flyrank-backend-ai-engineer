from fastapi import APIRouter, Depends, Header, Request, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas.billing import CheckoutRequest, CheckoutResponse
from app.services.stripe_service import StripeService
from app.services.invoice_service import InvoiceService
from app.services.proration_service import ProrationService
from app.services.quota_service import QuotaService
from app.models.plan import Plan
from datetime import datetime, timezone

router = APIRouter(tags=["billing"])


@router.post(
    "/billing/checkout-session",
    response_model=CheckoutResponse,
    summary="Create a Stripe Checkout Session for subscription upgrade"
)
def create_checkout(
    request: CheckoutRequest,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID", description="Tenant ID"),
    db: Session = Depends(get_db)
):
    if not x_tenant_id:
        raise HTTPException(
            status_code=400,
            detail={"error": "missing_header", "message": "Missing required header: 'X-Tenant-ID'"}
        )

    return StripeService.create_checkout_session(
        db=db,
        tenant_id=x_tenant_id,
        plan_code=request.plan_code
    )


@router.get(
    "/billing/invoice",
    summary="Generate an itemized monthly billing statement with detailed usage line items"
)
def get_monthly_invoice(
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID", description="Tenant ID"),
    db: Session = Depends(get_db)
):
    if not x_tenant_id:
        raise HTTPException(
            status_code=400,
            detail={"error": "missing_header", "message": "Missing required header: 'X-Tenant-ID'"}
        )

    return InvoiceService.generate_statement(db=db, tenant_id=x_tenant_id)


@router.get(
    "/billing/proration-preview",
    summary="Calculate exact mid-cycle upgrade proration and net amount due"
)
def preview_proration(
    target_plan_code: str = "pro",
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID", description="Tenant ID"),
    db: Session = Depends(get_db)
):
    if not x_tenant_id:
        raise HTTPException(
            status_code=400,
            detail={"error": "missing_header", "message": "Missing required header: 'X-Tenant-ID'"}
        )

    sub = QuotaService.get_tenant_subscription(db, x_tenant_id)
    target_plan = db.query(Plan).filter(Plan.code == target_plan_code).first()
    if not target_plan:
        raise HTTPException(status_code=404, detail={"error": "plan_not_found", "message": "Target plan not found."})

    now = datetime.now(timezone.utc)
    return ProrationService.calculate_mid_cycle_proration(
        period_start=sub.current_period_start,
        period_end=sub.current_period_end,
        upgrade_time=now,
        current_price_cents=sub.plan.price_cents,
        target_price_cents=target_plan.price_cents,
        current_plan_code=sub.plan.code,
        target_plan_code=target_plan.code
    )


@router.post(
    "/webhooks/stripe",
    summary="Stripe Webhook Receiver: signature verified and deduplicated"
)
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
    db: Session = Depends(get_db)
):
    payload = await request.body()
    event = StripeService.verify_webhook_signature(payload=payload, sig_header=stripe_signature)
    result = StripeService.process_webhook_event(db=db, event=event)
    return result
