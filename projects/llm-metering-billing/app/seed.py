from datetime import datetime, timezone, timedelta
from app.database import SessionLocal, Base, engine
from app.models.tenant import Tenant
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.usage_event import UsageEvent
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")


def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        logger.info("Seeding plans...")
        # 1. Plans
        free_plan = db.query(Plan).filter(Plan.code == "free").first()
        if not free_plan:
            free_plan = Plan(
                id="plan_free",
                code="free",
                name="Free Plan",
                api_call_limit=settings.free_plan_api_limit,
                token_limit=settings.free_plan_token_limit,
                price_cents=settings.free_plan_price_cents
            )
            db.add(free_plan)
        else:
            free_plan.api_call_limit = settings.free_plan_api_limit
            free_plan.token_limit = settings.free_plan_token_limit

        pro_plan = db.query(Plan).filter(Plan.code == "pro").first()
        if not pro_plan:
            pro_plan = Plan(
                id="plan_pro",
                code="pro",
                name="Pro Plan",
                api_call_limit=settings.pro_plan_api_limit,
                token_limit=settings.pro_plan_token_limit,
                price_cents=settings.pro_plan_price_cents
            )
            db.add(pro_plan)
        else:
            pro_plan.api_call_limit = settings.pro_plan_api_limit
            pro_plan.token_limit = settings.pro_plan_token_limit

        db.commit()

        now = datetime.now(timezone.utc)
        period_start = now - timedelta(days=5)
        period_end = now + timedelta(days=25)

        logger.info("Seeding demo tenants...")

        # 2. Demo Tenants
        # Tenant 1: Standard Free Tenant
        tenant_free = db.query(Tenant).filter(Tenant.id == "tenant_free").first()
        if not tenant_free:
            tenant_free = Tenant(
                id="tenant_free",
                name="Acme Startups (Free)",
                email="free@acme.test",
                stripe_customer_id="cus_free_demo_123"
            )
            db.add(tenant_free)
            db.commit()

        sub_free = db.query(Subscription).filter(Subscription.tenant_id == "tenant_free").first()
        if not sub_free:
            sub_free = Subscription(
                tenant_id="tenant_free",
                plan_id=free_plan.id,
                status="active",
                current_period_start=period_start,
                current_period_end=period_end
            )
            db.add(sub_free)
            db.commit()

        # Tenant 2: Standard Pro Tenant
        tenant_pro = db.query(Tenant).filter(Tenant.id == "tenant_pro").first()
        if not tenant_pro:
            tenant_pro = Tenant(
                id="tenant_pro",
                name="Global Scale Ltd (Pro)",
                email="billing@globalscale.test",
                stripe_customer_id="cus_pro_demo_456"
            )
            db.add(tenant_pro)
            db.commit()

        sub_pro = db.query(Subscription).filter(Subscription.tenant_id == "tenant_pro").first()
        if not sub_pro:
            sub_pro = Subscription(
                tenant_id="tenant_pro",
                plan_id=pro_plan.id,
                status="active",
                stripe_subscription_id="sub_pro_test_789",
                current_period_start=period_start,
                current_period_end=period_end
            )
            db.add(sub_pro)
            db.commit()

        # Tenant 3: Boundary Testing Tenant (at exactly 999 calls)
        tenant_boundary = db.query(Tenant).filter(Tenant.id == "tenant_boundary").first()
        if not tenant_boundary:
            tenant_boundary = Tenant(
                id="tenant_boundary",
                name="Edge Testing Org (Boundary 999)",
                email="edge@testing.test",
                stripe_customer_id="cus_boundary_demo_999"
            )
            db.add(tenant_boundary)
            db.commit()

        sub_boundary = db.query(Subscription).filter(Subscription.tenant_id == "tenant_boundary").first()
        if not sub_boundary:
            sub_boundary = Subscription(
                tenant_id="tenant_boundary",
                plan_id=free_plan.id,
                status="active",
                current_period_start=period_start,
                current_period_end=period_end
            )
            db.add(sub_boundary)
            db.commit()

        # Pre-seed 999 usage calls for tenant_boundary if not already there
        existing_calls = db.query(UsageEvent).filter(UsageEvent.tenant_id == "tenant_boundary").count()
        if existing_calls < 999:
            events_to_add = []
            for i in range(existing_calls, 999):
                events_to_add.append(
                    UsageEvent(
                        tenant_id="tenant_boundary",
                        event_type="generate",
                        input_tokens=50,
                        cached_input_tokens=0,
                        output_tokens=20,
                        reasoning_tokens=0,
                        cost_micros=325,
                        timestamp=period_start + timedelta(minutes=i)
                    )
                )
            db.bulk_save_objects(events_to_add)
            db.commit()
            logger.info("Pre-seeded 999 usage events for 'tenant_boundary'.")

        # Tenant 4: Unpaid/Past Due Tenant (to test 402 Payment Required)
        tenant_unpaid = db.query(Tenant).filter(Tenant.id == "tenant_unpaid").first()
        if not tenant_unpaid:
            tenant_unpaid = Tenant(
                id="tenant_unpaid",
                name="Past Due Ventures",
                email="unpaid@ventures.test",
                stripe_customer_id="cus_unpaid_demo_000"
            )
            db.add(tenant_unpaid)
            db.commit()

        sub_unpaid = db.query(Subscription).filter(Subscription.tenant_id == "tenant_unpaid").first()
        if not sub_unpaid:
            sub_unpaid = Subscription(
                tenant_id="tenant_unpaid",
                plan_id=pro_plan.id,
                status="past_due",
                stripe_subscription_id="sub_unpaid_test_000",
                current_period_start=period_start,
                current_period_end=period_end
            )
            db.add(sub_unpaid)
            db.commit()

        logger.info("Database seeding successfully completed!")
        logger.info("Tenants available:")
        logger.info(" - tenant_free: Active Free Plan (0/1000 calls)")
        logger.info(" - tenant_pro: Active Pro Plan (0/50000 calls)")
        logger.info(" - tenant_boundary: Free Plan at 999/1000 calls (ready for boundary test)")
        logger.info(" - tenant_unpaid: Pro Plan with status='past_due' (returns 402)")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

