"""
Reactive Fabric Core - Configuration
====================================

Pydantic-based configuration for reactive event system.
"""

from __future__ import annotations

# pylint: disable=too-few-public-methods

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


def create_reactive_settings() -> "ReactiveSettings":
    """Factory for ReactiveSettings."""
    return ReactiveSettings(
        max_events=1000,
        event_ttl=3600
    )


def create_service_settings() -> "ServiceSettings":
    """Factory for ServiceSettings."""
    return ServiceSettings(
        name="reactive-fabric-core",
        log_level="INFO"
    )


class ReactiveSettings(BaseSettings):
    """
    Reactive system settings.

    Attributes:
        max_events: Maximum events in buffer
        event_ttl: Event time-to-live in seconds
    """

    max_events: int = Field(
        default=1000,
        validation_alias="REACTIVE_MAX_EVENTS"
    )
    event_ttl: int = Field(
        default=3600,
        validation_alias="REACTIVE_EVENT_TTL"
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
        default="reactive-fabric-core",
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
        reactive: Reactive settings
        service: Service settings
    """

    reactive: ReactiveSettings = Field(default_factory=create_reactive_settings)
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
