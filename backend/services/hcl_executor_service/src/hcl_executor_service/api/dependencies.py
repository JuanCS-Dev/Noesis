"""
HCL Executor Service - Dependency Injection
===========================================

FastAPI dependency injection functions.
"""

from functools import lru_cache
from typing import Generator

from hcl_executor_service.config import Settings, get_settings
from hcl_executor_service.core.executor import ActionExecutor
from hcl_executor_service.core.k8s import KubernetesController
from hcl_executor_service.utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)


@lru_cache()
def get_cached_settings() -> Settings:
    """Get cached application settings."""
    return get_settings()


def get_k8s_controller() -> Generator[KubernetesController, None, None]:
    """
    Get Kubernetes Controller instance.

    Yields:
        KubernetesController instance
    """
    settings = get_cached_settings()
    controller = KubernetesController(settings.k8s)
    yield controller


def get_executor() -> Generator[ActionExecutor, None, None]:
    """
    Get Action Executor instance.

    Yields:
        ActionExecutor instance
    """
    settings = get_cached_settings()
    # Create controller manually or use dependency if we were in a route
    # Here we instantiate it directly to ensure scope correctness
    controller = KubernetesController(settings.k8s)
    executor = ActionExecutor(controller)
    yield executor


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
