"""BE-07: FastAPI structured LLM extract API."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from cost import log_usage
from provider import ProviderError, build_provider
from schemas import ExtractRequest, ExtractResponse
from settings import Settings, get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("ai_structured_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    logger.info(
        "startup llm_enabled=%s mock_llm=%s model=%s",
        settings.llm_enabled,
        settings.mock_llm,
        settings.openai_model,
    )
    yield


app = FastAPI(title="AI Structured Extract API", version="1.0.0", lifespan=lifespan)


@app.get("/health")
async def health():
    s: Settings = app.state.settings
    return {
        "status": "ok",
        "llm_enabled": s.llm_enabled,
        "mock_llm": s.mock_llm,
        "model": "mock-deterministic-v1" if s.mock_llm else s.openai_model,
    }


@app.post("/v1/extract", response_model=ExtractResponse)
async def extract(body: ExtractRequest):
    s: Settings = app.state.settings

    # Kill switch
    if not s.llm_enabled:
        raise HTTPException(
            status_code=503,
            detail="LLM calls disabled (LLM_ENABLED=false / kill switch)",
        )

    try:
        provider = build_provider(s)
    except ProviderError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    try:
        result, usage = await provider.extract(body.text)
    except ProviderError as e:
        log_usage(
            s.cost_log_path,
            provider=getattr(provider, "name", "unknown"),
            model=getattr(provider, "model", "unknown"),
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "cost_usd": 0.0},
            ok=False,
            extra={"error": str(e)[:200], "text_chars": len(body.text)},
        )
        raise HTTPException(status_code=502, detail=f"LLM provider failed: {e}") from e
    except Exception as e:
        # e.g. unexpected httpx.HTTPStatusError for 4xx
        log_usage(
            s.cost_log_path,
            provider=getattr(provider, "name", "unknown"),
            model=getattr(provider, "model", "unknown"),
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "cost_usd": 0.0},
            ok=False,
            extra={"error": str(e)[:200], "text_chars": len(body.text)},
        )
        raise HTTPException(status_code=502, detail=f"LLM call failed: {e}") from e

    log_usage(
        s.cost_log_path,
        provider=provider.name,
        model=provider.model,
        usage=usage,
        ok=True,
        extra={"text_chars": len(body.text)},
    )

    return ExtractResponse(
        result=result,
        provider=provider.name,  # type: ignore[arg-type]
        model=provider.model,
        usage=usage,
    )


@app.exception_handler(HTTPException)
async def http_exc_handler(_request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
