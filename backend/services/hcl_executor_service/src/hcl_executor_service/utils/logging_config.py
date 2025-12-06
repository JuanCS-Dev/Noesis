"""
HCL Executor Service - Logging Configuration
============================================

Structured logging configuration for the service.
"""

import logging
import sys
from typing import Any, Dict

import structlog


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure structured logging.
    
    Args:
        log_level: Logging level (default: "INFO")
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
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level.upper(),
    )


def get_logger(name: str) -> Any:
    """
    Get a structured logger.
    
    Args:
        name: Logger name
        
    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)
