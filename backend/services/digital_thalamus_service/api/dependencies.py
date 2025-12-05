"""
Digital Thalamus Service - API Dependencies
===========================================

Dependency injection for FastAPI endpoints.
"""

from __future__ import annotations


from config import Settings, get_settings
from core.router import RequestRouter
from core.validator import RequestValidator
from utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)

# Global instances
_router: RequestRouter | None = None
_validator: RequestValidator | None = None


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
    global _router  # pylint: disable=global-statement
    global _validator  # pylint: disable=global-statement

    _router = RequestRouter(settings.gateway)
    _validator = RequestValidator()


async def get_router() -> RequestRouter:
    """Dependency to get the router instance."""
    if _router is None:
        raise RuntimeError(
            "Router not initialized. Call initialize_service() first."
        )
    return _router


async def get_validator() -> RequestValidator:
    """Dependency to get the validator instance."""
    if _validator is None:
        raise RuntimeError(
            "Validator not initialized. Call initialize_service() first."
        )
    return _validator
