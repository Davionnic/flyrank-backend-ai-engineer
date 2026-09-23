from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class SimulatedUsage(BaseModel):
    input_tokens: int = Field(default=0, ge=0, description="Fresh input tokens")
    cached_input_tokens: int = Field(default=0, ge=0, description="Cached input tokens (discounted)")
    output_tokens: int = Field(default=0, ge=0, description="Standard output tokens")
    reasoning_tokens: int = Field(default=0, ge=0, description="Reasoning / thinking tokens (billed as output)")


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Prompt text to process")
    simulated_usage: Optional[SimulatedUsage] = Field(
        default_factory=SimulatedUsage,
        description="Simulated token counts to meter (no real model call needed)"
    )


class TokenBreakdown(BaseModel):
    standard_input: int
    cached_input: int
    standard_output: int
    reasoning_output: int
    effective_input_tokens: int
    effective_output_tokens: int
    total_tokens: int


class CostDetails(BaseModel):
    micros: int
    cents: int
    usd: str
    breakdown_micros: Dict[str, int]


class QuotaRemaining(BaseModel):
    api_calls_remaining: int
    tokens_remaining: int
    period_end: str


class GenerateResponse(BaseModel):
    status: str
    tenant_id: str
    plan: str
    tokens_billed: TokenBreakdown
    cost: CostDetails
    quota: QuotaRemaining

