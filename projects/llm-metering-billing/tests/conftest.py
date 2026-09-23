import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app as fastapi_app
import app.models.tenant
import app.models.plan
import app.models.subscription
import app.models.usage_event
import app.models.idempotency
import app.models.webhook_event
from app.models.tenant import Tenant
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.usage_event import UsageEvent
from app.models.idempotency import IdempotencyRecord
from app.models.webhook_event import ProcessedWebhookEvent
from sqlalchemy.pool import StaticPool

# Dedicated test database (in-memory SQLite with StaticPool so all connections share the same memory DB)
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()

    # Seed baseline plans
    free_plan = Plan(
        id="plan_free",
        code="free",
        name="Free Plan",
        api_call_limit=1000,
        token_limit=100000,
        price_cents=0
    )
    pro_plan = Plan(
        id="plan_pro",
        code="pro",
        name="Pro Plan",
        api_call_limit=50000,
        token_limit=10000000,
        price_cents=2900
    )
    session.add_all([free_plan, pro_plan])
    session.commit()

    now = datetime.now(timezone.utc)
    period_start = now - timedelta(days=2)
    period_end = now + timedelta(days=28)

    # Seed demo tenants
    tenant_free = Tenant(id="tenant_free", name="Free Tenant", email="free@test.com")
    tenant_pro = Tenant(id="tenant_pro", name="Pro Tenant", email="pro@test.com")
    tenant_boundary = Tenant(id="tenant_boundary", name="Boundary Tenant", email="boundary@test.com")
    tenant_unpaid = Tenant(id="tenant_unpaid", name="Unpaid Tenant", email="unpaid@test.com")

    session.add_all([tenant_free, tenant_pro, tenant_boundary, tenant_unpaid])
    session.commit()

    sub_free = Subscription(
        id="sub_free",
        tenant_id="tenant_free",
        plan_id=free_plan.id,
        status="active",
        current_period_start=period_start,
        current_period_end=period_end
    )
    sub_pro = Subscription(
        id="sub_pro",
        tenant_id="tenant_pro",
        plan_id=pro_plan.id,
        status="active",
        current_period_start=period_start,
        current_period_end=period_end
    )
    sub_boundary = Subscription(
        id="sub_boundary",
        tenant_id="tenant_boundary",
        plan_id=free_plan.id,
        status="active",
        current_period_start=period_start,
        current_period_end=period_end
    )
    sub_unpaid = Subscription(
        id="sub_unpaid",
        tenant_id="tenant_unpaid",
        plan_id=pro_plan.id,
        status="past_due",
        current_period_start=period_start,
        current_period_end=period_end
    )
    session.add_all([sub_free, sub_pro, sub_boundary, sub_unpaid])
    session.commit()

    # Pre-seed 999 calls for tenant_boundary
    boundary_events = [
        UsageEvent(
            tenant_id="tenant_boundary",
            event_type="generate",
            input_tokens=10,
            cached_input_tokens=0,
            output_tokens=10,
            reasoning_tokens=0,
            cost_micros=125,
            timestamp=period_start + timedelta(seconds=i)
        )
        for i in range(999)
    ]
    session.bulk_save_objects(boundary_events)
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()
