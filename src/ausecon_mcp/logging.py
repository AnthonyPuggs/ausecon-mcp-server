from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone

_NAMESPACE = "ausecon_mcp"
_CONFIGURED = False

_RESERVED_RECORD_KEYS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "message",
    "module",
    "msecs",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "taskName",
    "thread",
    "threadName",
}


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key in _RESERVED_RECORD_KEYS or key.startswith("_"):
                continue
            payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Attach a stderr JSON handler to the ausecon_mcp logger. Idempotent."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    level_name = os.environ.get("AUSECON_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(_JsonFormatter())

    logger = logging.getLogger(_NAMESPACE)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a logger scoped under the ausecon_mcp namespace."""
    if name.startswith(_NAMESPACE):
        return logging.getLogger(name)
    return logging.getLogger(f"{_NAMESPACE}.{name}")
