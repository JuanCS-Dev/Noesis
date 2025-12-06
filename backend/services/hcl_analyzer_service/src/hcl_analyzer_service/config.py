"""
HCL Analyzer Service - Configuration
====================================

Pydantic-based configuration management.
"""

from __future__ import annotations

# pylint: disable=too-few-public-methods

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class AnalyzerSettings(BaseSettings):
    """
    Analyzer specific settings.

    Attributes:
        anomaly_threshold: Threshold for anomaly detection (0.0 to 1.0)
        history_window_size: Number of historical data points to keep
    """

    anomaly_threshold: float = Field(default=0.8, validation_alias="ANALYZER_ANOMALY_THRESHOLD")
    history_window_size: int = Field(default=100, validation_alias="ANALYZER_HISTORY_WINDOW_SIZE")

    class Config:
        """Pydantic config."""
        env_file = ".env"
        populate_by_name = True


class ServiceSettings(BaseSettings):
    """
    General service settings.
    # pylint: disable=too-few-public-methods

    Attributes:
        name: Service name
        log_level: Logging level
    """

    name: str = Field(default="hcl-analyzer-service", validation_alias="SERVICE_NAME")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    class Config:
        """Pydantic config."""
        env_file = ".env"
        populate_by_name = True


def create_analyzer_settings() -> AnalyzerSettings:
    """Factory for AnalyzerSettings."""
    return AnalyzerSettings(anomaly_threshold=0.8, history_window_size=100)


def create_service_settings() -> ServiceSettings:
    """Factory for ServiceSettings."""
    return ServiceSettings(name="hcl-analyzer-service", log_level="INFO")


class Settings(BaseSettings):
    """
    Global application settings.

    Attributes:
        analyzer: Analyzer settings
        service: Service settings
    """

    analyzer: AnalyzerSettings = Field(default_factory=create_analyzer_settings)
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
