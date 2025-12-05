"""
Prefrontal Cortex Service - API Dependencies
============================================

Dependency injection for FastAPI endpoints.
"""

from __future__ import annotations

from config import Settings, get_settings
from core.decision_engine import DecisionEngine
from core.task_prioritizer import TaskPrioritizer
from utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)

# Global instances
_decision_engine: DecisionEngine | None = None
_task_prioritizer: TaskPrioritizer | None = None


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
    global _decision_engine  # pylint: disable=global-statement
    global _task_prioritizer  # pylint: disable=global-statement

    _decision_engine = DecisionEngine(settings.cognitive)
    _task_prioritizer = TaskPrioritizer(settings.cognitive)


async def get_decision_engine() -> DecisionEngine:
    """Dependency to get the decision engine instance."""
    if _decision_engine is None:
        raise RuntimeError(
            "Decision engine not initialized. Call initialize_service() first."
        )
    return _decision_engine


async def get_task_prioritizer() -> TaskPrioritizer:
    """Dependency to get the task prioritizer instance."""
    if _task_prioritizer is None:
        raise RuntimeError(
            "Task prioritizer not initialized. Call initialize_service() first."
        )
    return _task_prioritizer
