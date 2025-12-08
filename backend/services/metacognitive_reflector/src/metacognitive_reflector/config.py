"""
Metacognitive Reflector - Configuration
=======================================

Pydantic-based configuration for the Metacognitive Reflector service.

Memory Fortress Architecture:
- L1: Hot Cache (In-Memory) - <1ms latency
- L2: Warm Storage (Redis + AOF) - <10ms latency
- L3: Cold Storage (Qdrant) - <50ms latency
- L4: Vault (JSON + Checksums) - Disaster recovery
"""

from __future__ import annotations

# pylint: disable=too-few-public-methods

from functools import lru_cache
from pathlib import Path
from typing import Optional
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


def create_memory_settings() -> "MemorySettings":
    """Factory for MemorySettings."""
    return MemorySettings()


def create_redis_settings() -> "RedisSettings":
    """Factory for RedisSettings."""
    return RedisSettings()


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


class MemorySettings(BaseSettings):
    """
    Memory Fortress Configuration.
    
    Implements 4-tier memory architecture:
    - L1: Hot cache (in-memory)
    - L2: Warm storage (Redis)
    - L3: Cold storage (Qdrant via episodic-memory service)
    - L4: Vault (JSON backup)
    """
    # Episodic Memory Service (L3)
    service_url: str = Field(
        default="http://episodic-memory:8000",
        validation_alias="MEMORY_SERVICE_URL",
        description="URL of episodic memory service (Qdrant backend)"
    )
    timeout_seconds: float = Field(
        default=5.0,
        validation_alias="MEMORY_TIMEOUT",
        description="HTTP request timeout"
    )
    retry_attempts: int = Field(
        default=3,
        validation_alias="MEMORY_RETRY_ATTEMPTS",
        description="Number of retry attempts on failure"
    )
    retry_delay_seconds: float = Field(
        default=0.5,
        description="Delay between retries"
    )
    
    # Fallback and Backup (L4)
    fallback_enabled: bool = Field(
        default=True,
        validation_alias="MEMORY_FALLBACK_ENABLED",
        description="Enable in-memory fallback when service unavailable"
    )
    local_backup_path: str = Field(
        default="data/memory_backup",
        validation_alias="MEMORY_BACKUP_PATH",
        description="Directory for JSON backup files"
    )
    backup_interval_seconds: int = Field(
        default=300,  # 5 minutes
        description="Interval for syncing to vault backup"
    )
    
    # L1 Hot Cache
    cache_max_size: int = Field(
        default=1000,
        description="Maximum items in L1 hot cache"
    )
    cache_ttl_seconds: int = Field(
        default=300,  # 5 minutes
        description="TTL for L1 cache entries"
    )
    
    # Write-Ahead Log
    wal_enabled: bool = Field(
        default=True,
        description="Enable WAL for crash recovery"
    )
    wal_path: str = Field(
        default="data/wal",
        description="Directory for WAL files"
    )
    
    model_config = SettingsConfigDict(env_file=".env", populate_by_name=True, extra="ignore")


class RedisSettings(BaseSettings):
    """
    Redis Configuration for L2 Warm Storage.
    
    Persistence: AOF (Append-Only File) for durability.
    """
    url: str = Field(
        default="redis://localhost:6379",
        validation_alias="REDIS_URL",
        description="Redis connection URL"
    )
    password: Optional[str] = Field(
        default=None,
        validation_alias="REDIS_PASSWORD",
        description="Redis password (optional)"
    )
    db: int = Field(
        default=0,
        validation_alias="REDIS_DB",
        description="Redis database number"
    )
    
    # Connection Pool
    max_connections: int = Field(
        default=10,
        description="Maximum connections in pool"
    )
    socket_timeout: float = Field(
        default=5.0,
        description="Socket timeout in seconds"
    )
    
    # Key Prefixes
    penal_prefix: str = Field(
        default="noesis:penal:",
        description="Key prefix for penal records"
    )
    history_prefix: str = Field(
        default="noesis:history:",
        description="Key prefix for criminal history"
    )
    memory_prefix: str = Field(
        default="noesis:memory:",
        description="Key prefix for memory entries"
    )
    
    # TTL Defaults
    default_ttl_seconds: int = Field(
        default=604800,  # 7 days
        description="Default TTL for records"
    )
    
    model_config = SettingsConfigDict(env_file=".env", populate_by_name=True, extra="ignore")


class Settings(BaseSettings):
    """
    Global application settings.
    
    Memory Fortress Tiers:
    - L1: Hot Cache (in-memory) - MemorySettings.cache_*
    - L2: Warm Storage (Redis) - RedisSettings
    - L3: Cold Storage (Qdrant) - MemorySettings.service_url
    - L4: Vault (JSON) - MemorySettings.local_backup_path
    """
    service: ServiceSettings = Field(default_factory=create_service_settings)
    llm: LLMSettings = Field(default_factory=create_llm_settings)
    memory: MemorySettings = Field(default_factory=create_memory_settings)
    redis: RedisSettings = Field(default_factory=create_redis_settings)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def ensure_data_dirs(self) -> None:
        """Ensure data directories exist for memory persistence."""
        Path(self.memory.local_backup_path).mkdir(parents=True, exist_ok=True)
        if self.memory.wal_enabled:
            Path(self.memory.wal_path).mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    """
    settings = Settings()
    settings.ensure_data_dirs()
    return settings
