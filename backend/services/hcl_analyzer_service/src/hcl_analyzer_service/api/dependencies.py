"""
HCL Analyzer Service - Dependencies
===================================

FastAPI dependency injection.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Generator

from hcl_analyzer_service.config import Settings, get_settings
from hcl_analyzer_service.core.analyzer import SystemAnalyzer
from hcl_analyzer_service.utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)


@lru_cache()
def get_cached_settings() -> Settings:
    """Get cached application settings."""
    return get_settings()


def get_analyzer() -> Generator[SystemAnalyzer, None, None]:
    """
    Get System Analyzer instance.

    Yields:
        SystemAnalyzer instance
    """
    settings = get_cached_settings()
    analyzer = SystemAnalyzer(settings.analyzer)
    yield analyzer


def initialize_service() -> None:
    """Initialize service dependencies."""
    settings = get_cached_settings()

    # Setup structured logging
    setup_logging(settings.service.log_level)  # pylint: disable=no-member

    logger.info(
        "service_initializing",
        extra={
            "service_name": settings.service.name,  # pylint: disable=no-member
            "log_level": settings.service.log_level  # pylint: disable=no-member
        }
    )
