"""
Metacognitive Reflector - Configuration
=======================================

Pydantic-based configuration for the Metacognitive Reflector service.
"""

from __future__ import annotations

# pylint: disable=too-few-public-methods

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def create_service_settings() -> "ServiceSettings":
    """Factory for ServiceSettings."""
    return ServiceSettings(
        name="metacognitive-reflector",
        log_level="INFO"
    )


def create_llm_settings() -> "LLMSettings":
    """Factory for LLMSettings."""
    return LLMSettings(
        api_key="dummy_key",  # Default for tests
        model="gemini-3-pro-preview",  # Gemini 3 Pro (December 2025)
        thinking_level="high",
        max_tokens=8192
    )


class ServiceSettings(BaseSettings):
    """
    General service settings.
    """
    name: str = Field(
        default="metacognitive-reflector",
        validation_alias="SERVICE_NAME"
    )
    log_level: str = Field(
        default="INFO",
        validation_alias="LOG_LEVEL"
    )

    model_config = SettingsConfigDict(env_file=".env", populate_by_name=True, extra="ignore")


class LLMSettings(BaseSettings):
    """
    LLM configuration settings for Gemini 3 Pro (December 2025).
    """
    api_key: str = Field(..., validation_alias="GEMINI_API_KEY")
    model: str = Field(
        default="gemini-3-pro-preview",
        validation_alias="LLM_MODEL"
    )
    thinking_level: str = Field(
        default="high",
        validation_alias="LLM_THINKING_LEVEL",
        description="Gemini 3 reasoning depth: 'low' or 'high'"
    )
    max_tokens: int = Field(
        default=8192,
        validation_alias="LLM_MAX_TOKENS"
    )

    model_config = SettingsConfigDict(env_file=".env", populate_by_name=True, extra="ignore")


class Settings(BaseSettings):
    """
    Global application settings.
    """
    service: ServiceSettings = Field(default_factory=create_service_settings)
    llm: LLMSettings = Field(default_factory=create_llm_settings)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    """
    return Settings()
