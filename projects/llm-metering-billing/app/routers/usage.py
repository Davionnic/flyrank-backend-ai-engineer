from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas.usage import UsageRollupResponse
from app.services.meter_service import MeterService

router = APIRouter(tags=["usage"])


@router.get(
    "/usage",
    response_model=UsageRollupResponse,
    summary="Get tenant monthly usage rollup, limits, and cost breakdown"
)
def get_usage(
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID", description="Tenant ID"),
    db: Session = Depends(get_db)
):
    if not x_tenant_id:
        raise HTTPException(
            status_code=400,
            detail={"error": "missing_header", "message": "Missing required header: 'X-Tenant-ID'"}
        )

    return MeterService.get_usage_rollup(db=db, tenant_id=x_tenant_id)

