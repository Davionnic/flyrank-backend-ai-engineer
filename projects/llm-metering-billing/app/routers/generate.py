from fastapi import APIRouter, Depends, Header, Response, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas.generate import GenerateRequest, GenerateResponse
from app.services.pricing_engine import TokenUsage
from app.services.meter_service import MeterService

router = APIRouter(tags=["metering"])


@router.post(
    "/generate",
    response_model=GenerateResponse,
    summary="Simulated AI generation billable endpoint with idempotent metering",
    responses={
        200: {"description": "Usage successfully metered and allowed"},
        400: {"description": "Validation error or invalid request"},
        402: {"description": "Payment required / subscription lapsed or unpaid"},
        429: {"description": "Usage quota exceeded"},
        409: {"description": "Conflict: duplicate request with same idempotency key currently in-flight"}
    }
)
def generate_ai_completion(
    request: GenerateRequest,
    response: Response,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID", description="Tenant ID"),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key", description="Unique idempotency key"),
    db: Session = Depends(get_db)
):
    if not x_tenant_id:
        raise HTTPException(
            status_code=400,
            detail={"error": "missing_header", "message": "Missing required header: 'X-Tenant-ID'"}
        )

    sim_usage = request.simulated_usage
    token_usage = TokenUsage(
        input_tokens=sim_usage.input_tokens if sim_usage else 0,
        cached_input_tokens=sim_usage.cached_input_tokens if sim_usage else 0,
        output_tokens=sim_usage.output_tokens if sim_usage else 0,
        reasoning_tokens=sim_usage.reasoning_tokens if sim_usage else 0,
    )

    result_data, status_code, is_replay = MeterService.process_billable_request(
        db=db,
        tenant_id=x_tenant_id,
        path="/generate",
        payload=request.model_dump(),
        usage=token_usage,
        idempotency_key=idempotency_key,
        event_type="generate"
    )

    if is_replay:
        response.headers["X-Idempotent-Replay"] = "true"

    return result_data

