from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, timedelta
import uuid
from app.database import Base


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    key = Column(String, nullable=False, index=True)
    request_hash = Column(String, nullable=False)
    status = Column(String, nullable=False, default="processing")  # 'processing', 'completed', 'failed'
    response_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc) + timedelta(hours=24)
    )

    tenant = relationship("Tenant", back_populates="idempotency_records")

    __table_args__ = (
        UniqueConstraint("tenant_id", "key", name="uq_tenant_idempotency_key"),
    )

