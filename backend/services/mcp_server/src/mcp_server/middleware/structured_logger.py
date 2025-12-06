"""
Structured Logger Middleware
============================

JSON-based structured logging with trace IDs.

Follows CODE_CONSTITUTION: Measurable Quality.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any, Dict, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class StructuredLogger:
    """Structured logger with JSON output.

    Emits logs in JSON format with:
    - Timestamp
    - Log level
    - Message
    - Trace ID (for request correlation)
    - Additional context fields

    Example:
        >>> logger = StructuredLogger("mcp-server")
        >>> logger.info("Tool called", tool_name="tribunal_evaluate")
        {"timestamp": "2025-12-04T...", "level": "INFO", ...}
    """

    def __init__(self, service_name: str, log_level: str = "INFO"):
        """Initialize structured logger.

        Args:
            service_name: Name of service (appears in all logs)
            log_level: Minimum log level
        """
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(getattr(logging, log_level))

        # JSON formatter
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)

    def _log(
        self,
        level: str,
        message: str,
        trace_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Internal logging method.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            trace_id: Request trace ID (optional)
            **kwargs: Additional context fields
        """
        extra = {
            "service": self.service_name,
            "trace_id": trace_id or str(uuid.uuid4()),
            **kwargs,
        }

        log_method = getattr(self.logger, level.lower())
        log_method(message, extra=extra)

    def debug(
        self, message: str, trace_id: Optional[str] = None, **kwargs: Any
    ) -> None:
        """Log debug message."""
        self._log("DEBUG", message, trace_id, **kwargs)

    def info(
        self, message: str, trace_id: Optional[str] = None, **kwargs: Any
    ) -> None:
        """Log info message."""
        self._log("INFO", message, trace_id, **kwargs)

    def warning(
        self, message: str, trace_id: Optional[str] = None, **kwargs: Any
    ) -> None:
        """Log warning message."""
        self._log("WARNING", message, trace_id, **kwargs)

    def error(
        self, message: str, trace_id: Optional[str] = None, **kwargs: Any
    ) -> None:
        """Log error message."""
        self._log("ERROR", message, trace_id, **kwargs)

    def critical(
        self, message: str, trace_id: Optional[str] = None, **kwargs: Any
    ) -> None:
        """Log critical message."""
        self._log("CRITICAL", message, trace_id, **kwargs)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record

        Returns:
            JSON string
        """
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "service"):
            log_data["service"] = record.service
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id

        # Add any additional fields from extra
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "service",
                "trace_id",
            ]:
                log_data[key] = value

        return json.dumps(log_data)


class LoggingMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for request/response logging.

    Automatically logs:
    - Request method, path, and headers
    - Response status and duration
    - Trace ID for correlation

    Example:
        >>> app.add_middleware(LoggingMiddleware, logger=logger)
    """

    def __init__(self, app, logger: StructuredLogger):
        """Initialize middleware.

        Args:
            app: FastAPI application
            logger: Structured logger instance
        """
        super().__init__(app)
        self.logger = logger

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and log.

        Args:
            request: HTTP request
            call_next: Next middleware in chain

        Returns:
            HTTP response
        """
        # Generate trace ID
        trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))

        # Attach trace ID to request state
        request.state.trace_id = trace_id

        # Log request
        start_time = time.time()
        self.logger.info(
            "Request received",
            trace_id=trace_id,
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else None,
        )

        # Process request
        try:
            response = await call_next(request)

            # Log response
            duration = time.time() - start_time
            self.logger.info(
                "Request completed",
                trace_id=trace_id,
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2),
            )

            # Add trace ID to response headers
            response.headers["X-Trace-ID"] = trace_id

            return response

        except Exception as e:
            # Log error
            duration = time.time() - start_time
            self.logger.error(
                "Request failed",
                trace_id=trace_id,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=round(duration * 1000, 2),
            )
            raise
