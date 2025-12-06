"""
HCL Planner Service - Configuration Module
==========================================

Pydantic-based configuration management for the HCL Planner Service.
All configuration is loaded from environment variables with sensible defaults.
"""

from __future__ import annotations

from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class GeminiSettings(BaseSettings):
    """
    Configuration for Google Gemini integration.

    Attributes:
        api_key: Google Gemini API key
        model: Gemini model identifier
        thinking_level: Reasoning depth ("low" or "high")
        max_tokens: Maximum output tokens
        timeout: Request timeout in seconds
        temperature: Sampling temperature (0.0-1.0)
    """

    api_key: Optional[str] = Field(
        default=None,
        description="Google Gemini API key",
        alias="GEMINI_API_KEY"
    )
    model: str = Field(
        default="gemini-3.0-pro",
        description="Gemini model to use",
        alias="GEMINI_MODEL"
    )
    thinking_level: Literal["low", "high"] = Field(
        default="high",
        description="Reasoning depth",
        alias="GEMINI_THINKING_LEVEL"
    )
    max_tokens: int = Field(
        default=8192,
        description="Maximum output tokens",
        alias="GEMINI_MAX_TOKENS"
    )
    timeout: int = Field(
        default=120,
        description="Request timeout in seconds",
        alias="GEMINI_TIMEOUT"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Sampling temperature"
    )
    monthly_budget_usd: float = Field(
        default=200.0,
        ge=0.0,
        description="Monthly budget in USD for cost tracking",
        alias="GEMINI_MONTHLY_BUDGET_USD"
    )

    class Config:  # pylint: disable=too-few-public-methods,missing-class-docstring
        env_file = ".env"
        env_file_encoding = "utf-8"


class ServiceSettings(BaseSettings):
    """
    General service configuration.

    Attributes:
        name: Service identifier
        log_level: Logging level
    """

    name: str = Field(
        default="hcl-planner",
        description="Service identifier",
        alias="SERVICE_NAME"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level",
        alias="LOG_LEVEL"
    )

    class Config:  # pylint: disable=too-few-public-methods,missing-class-docstring
        env_file = ".env"
        env_file_encoding = "utf-8"


class Settings(BaseSettings):
    """
    Complete application settings.

    Combines all configuration sections.
    """

    service: ServiceSettings = Field(default_factory=ServiceSettings)
    gemini: GeminiSettings = Field(default_factory=GeminiSettings)

    class Config:  # pylint: disable=too-few-public-methods,missing-class-docstring
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """
    Get application settings.

    This function is cached by lru_cache for performance.
    Settings are loaded once and reused.

    Returns:
        Settings: Application configuration

    Example:
        >>> settings = get_settings()
        >>> print(settings.gemini.model)
        "gemini-3.0-pro"
    """
    return Settings()
