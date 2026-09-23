"""FlyRank BE-06 — Stage 2: POST/GET reports + make-report job."""
from __future__ import annotations

import uuid
from typing import Any

import inngest
import inngest.fast_api
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Report Jobs API", version="0.2.0")
inngest_client = inngest.Inngest(app_id="report-api")

# In-memory report store: id -> {status, topic, result?}
REPORTS: dict[str, dict[str, Any]] = {}


class ReportCreate(BaseModel):
    topic: str = Field(min_length=1)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/reports", status_code=202)
async def create_report(body: ReportCreate):
    report_id = str(uuid.uuid4())
    REPORTS[report_id] = {"id": report_id, "topic": body.topic, "status": "pending"}
    await inngest_client.send(
        inngest.Event(name="report/requested", data={"id": report_id, "topic": body.topic})
    )
    return {"id": report_id, "status": "pending"}


@app.get("/reports/{report_id}")
def get_report(report_id: str):
    report = REPORTS.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@inngest_client.create_function(
    fn_id="say-hello",
    trigger=inngest.TriggerEvent(event="test/hello"),
)
async def say_hello(ctx: inngest.Context, step: inngest.Step):
    await step.sleep("wait-five", 5)
    return {"ok": True, "msg": "hello from report-api"}


@inngest_client.create_function(
    fn_id="make-report",
    trigger=inngest.TriggerEvent(event="report/requested"),
)
async def make_report(ctx: inngest.Context, step: inngest.Step):
    report_id = ctx.event.data["id"]
    topic = ctx.event.data["topic"]

    await step.sleep("think", 8)

    def build() -> dict[str, Any]:
        result = {
            "headline": f"Report on {topic}",
            "summary": f"Background job finished a slow write-up about {topic}.",
            "bullets": [f"{topic} fact 1", f"{topic} fact 2", f"{topic} fact 3"],
        }
        if report_id in REPORTS:
            REPORTS[report_id]["status"] = "done"
            REPORTS[report_id]["result"] = result
        return result

    return await step.run("build-report", build)


inngest.fast_api.serve(app, inngest_client, [say_hello, make_report])
