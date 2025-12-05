"""
Maximus Core Service - Configuration
====================================

Pydantic-based configuration management.
"""

from __future__ import annotations

# pylint: disable=too-few-public-methods

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


def create_coordination_settings() -> "CoordinationSettings":
    """Factory for CoordinationSettings."""
    return CoordinationSettings(
        health_check_interval=30.0,
        service_timeout=5.0
    )


def create_service_settings() -> "ServiceSettings":
    """Factory for ServiceSettings."""
    return ServiceSettings(
        name="maximus-core-service",
        log_level="INFO"
    )


class CoordinationSettings(BaseSettings):  # pylint: disable=too-few-public-methods
    """
    Coordination specific settings.

    Attributes:
        health_check_interval: Interval in seconds for health checks
        service_timeout: Timeout in seconds for service calls
    """

    health_check_interval: float = Field(
        default=30.0,
        validation_alias="COORDINATION_HEALTH_CHECK_INTERVAL"
    )
    service_timeout: float = Field(
        default=5.0,
        validation_alias="COORDINATION_SERVICE_TIMEOUT"
    )

    class Config:
        """Pydantic config."""
        env_file = ".env"
        populate_by_name = True


class ServiceSettings(BaseSettings):  # pylint: disable=too-few-public-methods
    """
    General service settings.

    Attributes:
        name: Service name
        log_level: Logging level
    """

    name: str = Field(
        default="maximus-core-service",
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


class Settings(BaseSettings):  # pylint: disable=too-few-public-methods
    """
    Global application settings.

    Attributes:
        coordination: Coordination settings
        service: Service settings
    """

    coordination: CoordinationSettings = Field(
        default_factory=create_coordination_settings
    )
    service: ServiceSettings = Field(
        default_factory=create_service_settings
    )

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
