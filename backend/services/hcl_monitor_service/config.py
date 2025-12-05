"""
HCL Monitor Service - Configuration
===================================

Pydantic-based configuration management.
"""
# pylint: disable=too-few-public-methods

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


def create_monitor_settings() -> "MonitorSettings":
    """Factory for MonitorSettings."""
    return MonitorSettings(collection_interval=1.0, history_max_size=100)


def create_service_settings() -> "ServiceSettings":
    """Factory for ServiceSettings."""
    return ServiceSettings(name="hcl-monitor-service", log_level="INFO")


class MonitorSettings(BaseSettings):  # pylint: disable=too-few-public-methods
    """
    Monitor specific settings.

    Attributes:
        collection_interval: Interval in seconds between metric collections
        history_max_size: Maximum number of historical data points to keep
    """

    collection_interval: float = Field(default=1.0, validation_alias="MONITOR_COLLECTION_INTERVAL")
    history_max_size: int = Field(default=100, validation_alias="MONITOR_HISTORY_MAX_SIZE")

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

    name: str = Field(default="hcl-monitor-service", validation_alias="SERVICE_NAME")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    class Config:
        """Pydantic config."""
        env_file = ".env"
        populate_by_name = True


class Settings(BaseSettings):  # pylint: disable=too-few-public-methods
    """
    Global application settings.

    Attributes:
        monitor: Monitor settings
        service: Service settings
    """

    monitor: MonitorSettings = Field(default_factory=create_monitor_settings)
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
