"""
Maximus Core Service - API Dependencies
=======================================

Dependency injection for FastAPI endpoints.
"""

from __future__ import annotations


from ..config import Settings, get_settings
from ..core.coordinator import SystemCoordinator
from ..core.health_aggregator import HealthAggregator
from ..utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)

# Global instances
_coordinator: SystemCoordinator | None = None
_health_aggregator: HealthAggregator | None = None


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

    # Initialize core components
    global _coordinator  # pylint: disable=global-statement
    global _health_aggregator  # pylint: disable=global-statement

    _coordinator = SystemCoordinator(settings.coordination)
    _health_aggregator = HealthAggregator()


async def get_coordinator() -> SystemCoordinator:
    """Dependency to get the coordinator instance."""
    if _coordinator is None:
        raise RuntimeError(
            "Coordinator not initialized. Call initialize_service() first."
        )
    return _coordinator


async def get_health_aggregator() -> HealthAggregator:
    """Dependency to get the health aggregator instance."""
    if _health_aggregator is None:
        raise RuntimeError(
            "Health aggregator not initialized. Call initialize_service() first."
        )
    return _health_aggregator
