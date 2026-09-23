from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    plan_id = Column(String, ForeignKey("plans.id"), nullable=False, index=True)
    stripe_subscription_id = Column(String, nullable=True, unique=True, index=True)
    status = Column(String, nullable=False, default="active")  # active, past_due, canceled
    current_period_start = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    current_period_end = Column(DateTime, nullable=False)

    tenant = relationship("Tenant", back_populates="subscription")
    plan = relationship("Plan", back_populates="subscriptions")

