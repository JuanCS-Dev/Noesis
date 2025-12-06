"""
Digital Thalamus Service - Configuration
========================================

Pydantic-based configuration management for API Gateway.
"""

from __future__ import annotations

# pylint: disable=too-few-public-methods

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


def create_gateway_settings() -> "GatewaySettings":
    """Factory for GatewaySettings."""
    return GatewaySettings(
        request_timeout=30.0,
        max_retries=3
    )


def create_service_settings() -> "ServiceSettings":
    """Factory for ServiceSettings."""
    return ServiceSettings(
        name="digital-thalamus-service",
        log_level="INFO"
    )


class GatewaySettings(BaseSettings):
    """
    Gateway specific settings.

    Attributes:
        request_timeout: Timeout in seconds for forwarded requests
        max_retries: Maximum number of retry attempts for failed requests
    """

    request_timeout: float = Field(
        default=30.0,
        validation_alias="GATEWAY_REQUEST_TIMEOUT"
    )
    max_retries: int = Field(
        default=3,
        validation_alias="GATEWAY_MAX_RETRIES"
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
        default="digital-thalamus-service",
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
        gateway: Gateway settings
        service: Service settings
    """

    gateway: GatewaySettings = Field(default_factory=create_gateway_settings)
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
