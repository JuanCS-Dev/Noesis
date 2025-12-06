"""
HCL Planner Service - Structured Logging Configuration
======================================================

Provides structured logging setup following Google SRE practices.
All logs are JSON-formatted with contextual metadata.
"""

from __future__ import annotations

import logging
import sys
from typing import Any, Dict
import json
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Outputs logs as JSON with standard fields:
        - timestamp: ISO 8601 timestamp
        - level: Log level (INFO, ERROR, etc.)
        - logger: Logger name
        - message: Log message
        - context: Additional context (from extra={})
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra context
        if hasattr(record, "context"):
            log_data["context"] = record.context

        # Add any extra fields from extra={}
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName",
                "relativeCreated", "thread", "threadName", "exc_info",
                "exc_text", "stack_info", "context"
            ]:
                log_data[key] = value

        return json.dumps(log_data)


def setup_logging(level: str = "INFO") -> None:
    """
    Setup structured logging for the application.

    Configures root logger with JSON formatter and console handler.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Example:
        >>> setup_logging("DEBUG")
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("test", extra={"user_id": 123})
    """
    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler with structured formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())

    # Configure root logger
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, level.upper()))


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info(
        ...     "plan_generated",
        ...     extra={"plan_id": "abc123", "action_count": 3}
        ... )
    """
    return logging.getLogger(name)
