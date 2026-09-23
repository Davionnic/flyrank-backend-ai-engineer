from pydantic import BaseModel, Field
from typing import Optional


class CheckoutRequest(BaseModel):
    plan_code: str = Field(default="pro", description="Plan code to subscribe to ('pro')")


class CheckoutResponse(BaseModel):
    status: str
    checkout_url: str
    session_id: str
    tenant_id: str
    plan: str
    note: Optional[str] = None

