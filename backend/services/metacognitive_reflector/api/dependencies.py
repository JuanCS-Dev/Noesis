"""
Metacognitive Reflector - API Dependencies
==========================================

Dependency injection for FastAPI endpoints.
"""

from __future__ import annotations


from ..config import Settings, get_settings
from ..core.memory_client import MemoryClient
from ..core.reflector import Reflector
from ..utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)

# Global instances
_reflector: Reflector | None = None
_memory_client: MemoryClient | None = None


def get_cached_settings() -> Settings:
    """Dependency to get cached settings."""
    return get_settings()


def initialize_service() -> None:
    """Initialize service components."""
    settings = get_cached_settings()

    # Setup logging
    setup_logging(settings.service.log_level)

    logger.info(
        "service_initializing",
        service_name=settings.service.name,
        log_level=settings.service.log_level
    )

    # Initialize core components
    global _reflector, _memory_client  # pylint: disable=global-statement
    _reflector = Reflector(settings)
    _memory_client = MemoryClient()


async def get_reflector() -> Reflector:
    """Dependency to get the reflector instance."""
    if _reflector is None:
        raise RuntimeError("Reflector not initialized.")
    return _reflector


async def get_memory_client() -> MemoryClient:
    """Dependency to get the memory client instance."""
    if _memory_client is None:
        raise RuntimeError("Memory client not initialized.")
    return _memory_client
