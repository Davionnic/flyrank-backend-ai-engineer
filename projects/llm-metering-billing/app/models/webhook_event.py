from sqlalchemy import Column, String, DateTime
from datetime import datetime, timezone
import uuid
from app.database import Base


class ProcessedWebhookEvent(Base):
    __tablename__ = "processed_webhook_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    stripe_event_id = Column(String, unique=True, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    processed_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

