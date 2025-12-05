"""
HCL Monitor Service - API Dependencies
======================================

Dependency injection for FastAPI endpoints.
"""

from ..config import Settings, get_settings
from ..core.collector import SystemMetricsCollector
from ..utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)

# Global collector instance
_collector: SystemMetricsCollector | None = None


def get_cached_settings() -> Settings:
    """Dependency to get cached settings."""
    return get_settings()


def initialize_service() -> None:
    """Initialize service components."""
    settings = get_cached_settings()

    # Setup logging
    setup_logging(settings.service.log_level)  # pylint: disable=no-member

    logger.info(
        "service_initializing",
        service_name=settings.service.name,  # pylint: disable=no-member
        log_level=settings.service.log_level  # pylint: disable=no-member
    )

    # Initialize collector
    global _collector  # pylint: disable=global-statement
    _collector = SystemMetricsCollector(settings.monitor)


async def get_collector() -> SystemMetricsCollector:
    """Dependency to get the metrics collector instance."""
    if _collector is None:
        raise RuntimeError("Collector not initialized. Call initialize_service() first.")
    return _collector
