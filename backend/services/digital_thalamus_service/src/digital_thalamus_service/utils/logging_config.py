"""
Digital Thalamus Service - Logging Configuration
================================================

Structured logging configuration with request tracing.
"""

from __future__ import annotations


import logging
import sys
from typing import Any

import structlog


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure structured logging.

    Args:
        log_level: Logging level (default: INFO)
    """
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    structlog.configure(
        processors=shared_processors + [
            structlog.processors.JSONRenderer()
        ],
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(log_level)
        ),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )


def get_logger(name: str) -> Any:
    """
    Get a structured logger instance.

    Args:
        name: Logger name

    Returns:
        Structured logger
    """
    return structlog.get_logger(name)
