import json
import logging
import os
import sys
import threading
import time
from typing import Any, Dict, Optional


_local_ctx = threading.local()


def set_log_context(**kwargs: Any) -> None:
    ctx = getattr(_local_ctx, "ctx", {})
    ctx.update(kwargs)
    _local_ctx.ctx = ctx


class JsonLogFormatter(logging.Formatter):
    def __init__(self, debug_trace: bool = False):
        super().__init__()
        self.debug_trace = debug_trace

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        payload: Dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # context
        ctx: Dict[str, Any] = getattr(_local_ctx, "ctx", {})
        if ctx:
            payload.update(ctx)
        # include extras if any
        for key, value in record.__dict__.items():
            if key in ("args", "msg", "exc_info", "exc_text", "stack_info", "lineno", "funcName", "pathname"):
                continue
            if key.startswith("_"):
                continue
            if key not in payload:
                try:
                    json.dumps(value)
                    payload[key] = value
                except Exception:
                    payload[key] = str(value)
        if self.debug_trace:
            payload["trace"] = True
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(verbosity: int = 1, debug_trace: bool = False) -> None:
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter(debug_trace=debug_trace))

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)
