"""FlyRank BE-06 — Stage 1: FastAPI + Inngest say-hello."""
from __future__ import annotations

import inngest
import inngest.fast_api
from fastapi import FastAPI

app = FastAPI(title="Report Jobs API", version="0.1.0")
inngest_client = inngest.Inngest(app_id="report-api")


@app.get("/health")
def health():
    return {"status": "ok"}


@inngest_client.create_function(
    fn_id="say-hello",
    trigger=inngest.TriggerEvent(event="test/hello"),
)
async def say_hello(ctx: inngest.Context, step: inngest.Step):
    await step.sleep("wait-five", 5)
    return {"ok": True, "msg": "hello from report-api"}


inngest.fast_api.serve(app, inngest_client, [say_hello])
