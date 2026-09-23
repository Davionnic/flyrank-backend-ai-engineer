from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, unique=True, nullable=False, index=True)  # 'free', 'pro'
    name = Column(String, nullable=False)
    api_call_limit = Column(Integer, nullable=False)
    token_limit = Column(Integer, nullable=False)
    price_cents = Column(Integer, nullable=False)  # stored in integer cents

    subscriptions = relationship("Subscription", back_populates="plan")

