import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.config import settings
from app.database import engine, Base
from app.routers import generate_router, usage_router, billing_router

# Configure clean logging (never log secrets)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("billing_engine")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Usage Metering & Billing Engine...")
    # Ensure database schema is created
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized.")
    yield
    logger.info("Shutting down Usage Metering & Billing Engine...")


app = FastAPI(
    title="Usage Metering & Billing Engine",
    description="Multi-tenant SaaS metering, honest quota enforcement, AI token cost engine, and Stripe test billing.",
    version="1.0.0",
    lifespan=lifespan
)

# Custom validation error format
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        errors.append({"field": loc, "message": err.get("msg")})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validation_error",
            "message": "Input validation failed. Please check your request parameters.",
            "details": errors
        }
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    headers = getattr(exc, "headers", None) or {}
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail, headers=headers)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "http_error", "message": exc.detail},
        headers=headers
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error processing {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. The incident has been recorded."
        }
    )


# Health check endpoint
@app.get("/health", tags=["system"])
def health_check():
    return {
        "status": "healthy",
        "service": "usage-metering-billing-engine",
        "env": settings.app_env,
        "database": "connected"
    }


# Include Routers
app.include_router(generate_router)
app.include_router(usage_router)
app.include_router(billing_router)

