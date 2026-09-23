"""FlyRank BE-06 — FastAPI + Inngest background report jobs."""
from __future__ import annotations

import logging
import os
import uuid
from typing import Any

import inngest
import inngest.fast_api
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Local Dev Server: no cloud signing key required.
os.environ.setdefault("INNGEST_DEV", "1")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("report-api")

app = FastAPI(title="Report Jobs API", version="1.0.0")
inngest_client = inngest.Inngest(app_id="report-api", is_production=False)

REPORTS: dict[str, dict[str, Any]] = {}


class ReportCreate(BaseModel):
    topic: str = Field(min_length=1)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/reports", status_code=202)
async def create_report(body: ReportCreate):
    topic = (body.topic or "").strip()
    if not topic:
        # Client validation error — do not enqueue; retries would never help.
        raise HTTPException(status_code=400, detail="topic is required")

    report_id = str(uuid.uuid4())
    REPORTS[report_id] = {"id": report_id, "topic": topic, "status": "pending"}
    await inngest_client.send(
        inngest.Event(name="report/requested", data={"id": report_id, "topic": topic})
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
    retries=2,
)
async def make_report(ctx: inngest.Context, step: inngest.Step):
    report_id = ctx.event.data["id"]
    topic = ctx.event.data["topic"]

    await step.sleep("think", 8)

    def build() -> dict[str, Any]:
        if topic == "fail":
            if report_id in REPORTS:
                REPORTS[report_id]["status"] = "failed"
            raise RuntimeError("The report oven is broken!")

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


@inngest_client.create_function(
    fn_id="heartbeat",
    trigger=inngest.TriggerCron(cron="* * * * *"),
)
async def heartbeat(ctx: inngest.Context, step: inngest.Step):
    def summarize() -> dict[str, int]:
        counts = {"pending": 0, "done": 0, "failed": 0}
        for r in REPORTS.values():
            status = r.get("status")
            if status in counts:
                counts[status] += 1
        log.info(
            "heartbeat pending=%s done=%s failed=%s total=%s",
            counts["pending"],
            counts["done"],
            counts["failed"],
            len(REPORTS),
        )
        return counts

    return await step.run("count-reports", summarize)


inngest.fast_api.serve(app, inngest_client, [say_hello, make_report, heartbeat])
