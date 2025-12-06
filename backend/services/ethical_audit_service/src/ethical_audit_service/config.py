"""
Ethical Audit Service - Configuration
=====================================

Pydantic-based configuration management for Guardian Agent.
"""

from __future__ import annotations

# pylint: disable=too-few-public-methods

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


def create_audit_settings() -> "AuditSettings":
    """Factory for AuditSettings."""
    return AuditSettings(
        enable_blocking=False,
        max_violations_per_hour=100
    )


def create_service_settings() -> "ServiceSettings":
    """Factory for ServiceSettings."""
    return ServiceSettings(
        name="ethical-audit-service",
        log_level="INFO"
    )


class AuditSettings(BaseSettings):
    """
    Audit and compliance settings.

    Attributes:
        enable_blocking: Whether to block non-compliant operations
        max_violations_per_hour: Maximum violations logged per hour
    """

    enable_blocking: bool = Field(
        default=False,
        validation_alias="AUDIT_ENABLE_BLOCKING"
    )
    max_violations_per_hour: int = Field(
        default=100,
        validation_alias="AUDIT_MAX_VIOLATIONS_PER_HOUR"
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
        default="ethical-audit-service",
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
        audit: Audit settings
        service: Service settings
    """

    audit: AuditSettings = Field(default_factory=create_audit_settings)
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
