"""
Reactive Fabric Core - API Dependencies
=======================================

Dependency injection for FastAPI endpoints.
"""

from __future__ import annotations


from ..config import Settings, get_settings
from ..core.event_bus import EventBus
from ..utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)

# Global instance
_event_bus: EventBus | None = None


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

    # Initialize event bus
    global _event_bus  # pylint: disable=global-statement
    _event_bus = EventBus(settings.reactive)


async def get_event_bus() -> EventBus:
    """Dependency to get the event bus instance."""
    if _event_bus is None:
        raise RuntimeError(
            "Event bus not initialized. Call initialize_service() first."
        )
    return _event_bus
