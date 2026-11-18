"""
Structured JSON Logging and Correlation ID Tracking.
Phase 11 — Step 11.1: Configures structured JSON log formatters and ASGI correlation middleware.
"""

import json
import logging
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable to store correlation ID across async request tasks
correlation_id_ctx: ContextVar[Optional[str]] = ContextVar("correlation_id_ctx", default=None)


class JSONFormatter(logging.Formatter):
    """Formats log records as structured, machine-parsable JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "correlation_id": correlation_id_ctx.get() or "none",
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_structured_logging(level: int = logging.INFO) -> logging.Logger:
    """Configures root logger with JSONFormatter for production log aggregation."""
    logger = logging.getLogger("market_sentinel")
    logger.setLevel(level)

    # Avoid duplicate handlers if re-initialized
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.propagate = False

    return logger


logger = setup_structured_logging()


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware ensuring every HTTP request carries an X-Correlation-ID.
    If provided by client/upstream proxy, it is preserved; otherwise, a UUID4 is generated.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        corr_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        token = correlation_id_ctx.set(corr_id)

        try:
            logger.info(f"Incoming request {request.method} {request.url.path}")
            response: Response = await call_next(request)
            response.headers["X-Correlation-ID"] = corr_id
            return response
        finally:
            correlation_id_ctx.reset(token)
