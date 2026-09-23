from pydantic import BaseModel
from typing import Dict


class PlanInfo(BaseModel):
    code: str
    name: str
    status: str


class BillingPeriod(BaseModel):
    start: str
    end: str


class MetricUsage(BaseModel):
    used: int
    limit: int
    remaining: int
    percentage_used: float


class TokenMetricUsage(MetricUsage):
    breakdown: Dict[str, int]


class CostRollup(BaseModel):
    total_micros: int
    total_cents: int
    formatted_usd: str


class UsageRollupResponse(BaseModel):
    tenant_id: str
    plan: PlanInfo
    billing_period: BillingPeriod
    api_calls: MetricUsage
    tokens: TokenMetricUsage
    cost: CostRollup

