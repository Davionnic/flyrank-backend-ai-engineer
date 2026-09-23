"""FlyRank BE-06 — background report jobs (FastAPI + Inngest)."""
from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="Report Jobs API", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}
