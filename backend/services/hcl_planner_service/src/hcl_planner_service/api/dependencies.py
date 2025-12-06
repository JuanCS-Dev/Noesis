"""
HCL Planner Service - Dependency Injection
==========================================

FastAPI dependency injection functions.

Provides injectable dependencies for Settings, Agentic Planner, Logging.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Generator

from hcl_planner_service.config import Settings, get_settings
from hcl_planner_service.core import AgenticPlanner
from hcl_planner_service.utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)


@lru_cache()
def get_cached_settings() -> Settings:
    """
    Get cached application settings.

    Settings are loaded once and cached for performance.
    Thread-safe via lru_cache.

    Returns:
        Application settings
    """
    return get_settings()


def get_planner() -> Generator[AgenticPlanner, None, None]:
    """
    Get Agentic Planner instance.

    Creates planner with current settings. Planner is created
    once per request and cleaned up afterward.

    Yields:
        AgenticPlanner instance

    Example:
        >>> @app.post("/plan")
        >>> async def generate_plan(
        ...     request: PlanRequest,
        ...     planner: AgenticPlanner = Depends(get_planner)
        ... ):
        ...     return await planner.recommend_actions(...)
    """
    settings = get_cached_settings()
    planner = AgenticPlanner(settings.gemini)

    try:
        yield planner
    finally:
        # Cleanup if needed (planner is stateless, so no cleanup required)
        pass


def initialize_service() -> None:
    """
    Initialize service dependencies.

    Called during application startup to:
        - Setup logging
        - Load configuration
        - Log startup info
    """
    settings = get_cached_settings()

    # Setup structured logging
    setup_logging(settings.service.log_level)  # pylint: disable=no-member

    logger.info(
        "service_initializing",
        extra={
            "service_name": settings.service.name,  # pylint: disable=no-member
            "gemini_model": settings.gemini.model,  # pylint: disable=no-member
            "log_level": settings.service.log_level  # pylint: disable=no-member
        }
    )
