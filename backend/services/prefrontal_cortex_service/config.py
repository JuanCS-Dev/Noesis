"""
Prefrontal Cortex Service - Configuration
=========================================

Pydantic-based configuration management for executive cognitive functions.
"""

from __future__ import annotations

# pylint: disable=too-few-public-methods

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


def create_cognitive_settings() -> "CognitiveSettings":
    """Factory for CognitiveSettings."""
    return CognitiveSettings(
        decision_timeout=10.0,
        max_tasks=100
    )


def create_service_settings() -> "ServiceSettings":
    """Factory for ServiceSettings."""
    return ServiceSettings(
        name="prefrontal-cortex-service",
        log_level="INFO"
    )


class CognitiveSettings(BaseSettings):
    """
    Cognitive executive settings.

    Attributes:
        decision_timeout: Timeout in seconds for decision-making
        max_tasks: Maximum number of tasks to manage simultaneously
    """

    decision_timeout: float = Field(
        default=10.0,
        validation_alias="COGNITIVE_DECISION_TIMEOUT"
    )
    max_tasks: int = Field(
        default=100,
        validation_alias="COGNITIVE_MAX_TASKS"
    )

    class Config:
        """Pydantic config."""
        env_file = ".env"
        populate_by_name = True


class ServiceSettings(BaseSettings):
    """
    General service settings.

    Attributes:
        name: Service name
        log_level: Logging level
    """

    name: str = Field(
        default="prefrontal-cortex-service",
        validation_alias="SERVICE_NAME"
    )
    log_level: str = Field(
        default="INFO",
        validation_alias="LOG_LEVEL"
    )

    class Config:
        """Pydantic config."""
        env_file = ".env"
        populate_by_name = True


class Settings(BaseSettings):
    """
    Global application settings.

    Attributes:
        cognitive: Cognitive settings
        service: Service settings
    """

    cognitive: CognitiveSettings = Field(default_factory=create_cognitive_settings)
    service: ServiceSettings = Field(default_factory=create_service_settings)

    class Config:
        """Pydantic config."""
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings object
    """
    return Settings()
