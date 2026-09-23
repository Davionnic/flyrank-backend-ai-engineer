"""Append-only cost / usage logging as JSON lines."""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("ai_structured_api.cost")
_lock = threading.Lock()


def log_usage(
    path: str,
    *,
    provider: str,
    model: str,
    usage: dict[str, int | float],
    ok: bool,
    extra: dict[str, Any] | None = None,
) -> None:
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "provider": provider,
        "model": model,
        "ok": ok,
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0),
        "cost_usd": usage.get("cost_usd", 0.0),
    }
    if extra:
        record.update(extra)

    line = json.dumps(record, separators=(",", ":"))
    # Always emit a structured log line (visible in uvicorn)
    logger.info("cost %s", line)

    target = Path(path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with _lock:
            with target.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
    except OSError as e:
        logger.warning("failed to write cost log %s: %s", path, e)
