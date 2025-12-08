"""
LLM Configuration - Multi-Provider Support
==========================================

Supports:
- Nebius Token Factory (Primary - OpenAI-compatible)
- Google Gemini (Fallback)

Reference:
- Nebius Docs: https://docs.tokenfactory.nebius.com/quickstart
- Cookbook: https://github.com/nebius/token-factory-cookbook
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import os


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    NEBIUS = "nebius"
    GEMINI = "gemini"
    AUTO = "auto"  # Auto-select based on available keys


@dataclass
class NebiusConfig:
    """
    Nebius Token Factory Configuration.
    
    API: OpenAI-compatible
    URL: https://api.tokenfactory.nebius.com/v1/
    
    Recommended Models (Dec 2025):
    - deepseek-ai/DeepSeek-R1-0528 (Reasoning, best for metacognition)
    - Qwen/Qwen3-235B-A22B (General, large context)
    - meta-llama/Llama-3.3-70B-Instruct (Fast inference)
    
    Attributes:
        api_key: Nebius API key (from NEBIUS_API_KEY env)
        base_url: API endpoint
        model: Model identifier
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum output tokens
        timeout: Request timeout in seconds
    """
    api_key: str = field(
        default_factory=lambda: os.getenv("NEBIUS_API_KEY", "")
    )
    base_url: str = "https://api.tokenfactory.nebius.com/v1/"
    
    # DeepSeek-R1 is optimal for metacognitive reasoning
    model: str = field(
        default_factory=lambda: os.getenv(
            "NEBIUS_MODEL",
            "deepseek-ai/DeepSeek-R1-0528"
        )
    )
    
    temperature: float = 0.7
    max_tokens: int = 8192
    timeout: int = 120
    
    # Nebius-specific options
    stream: bool = False
    
    @property
    def is_configured(self) -> bool:
        """Check if Nebius is properly configured."""
        return bool(self.api_key and len(self.api_key) > 10)
    
    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError(f"temperature must be 0-2, got {self.temperature}")
        if self.max_tokens < 1:
            raise ValueError(f"max_tokens must be positive, got {self.max_tokens}")


@dataclass
class GeminiConfig:
    """
    Google Gemini Configuration (Fallback).
    
    Used when Nebius is unavailable or for specific use cases.
    
    Attributes:
        api_key: Google API key (from GEMINI_API_KEY env)
        model: Gemini model identifier
        thinking_level: Reasoning depth ('low' or 'high')
        temperature: Sampling temperature
        max_tokens: Maximum output tokens
        timeout: Request timeout in seconds
    """
    api_key: str = field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY", "")
    )
    model: str = field(
        default_factory=lambda: os.getenv(
            "GEMINI_MODEL",
            "gemini-2.0-flash"
        )
    )
    thinking_level: str = "high"
    temperature: float = 0.7
    max_tokens: int = 8192
    timeout: int = 120
    
    @property
    def is_configured(self) -> bool:
        """Check if Gemini is properly configured."""
        return bool(self.api_key and len(self.api_key) > 10)


@dataclass
class LLMConfig:
    """
    Unified LLM Configuration.
    
    Manages provider selection and configuration.
    Priority: Nebius > Gemini
    
    Attributes:
        provider: Which provider to use (auto, nebius, gemini)
        nebius: Nebius-specific configuration
        gemini: Gemini-specific configuration
        retry_attempts: Number of retry attempts on failure
        retry_delay: Delay between retries in seconds
    """
    provider: LLMProvider = LLMProvider.AUTO
    nebius: NebiusConfig = field(default_factory=NebiusConfig)
    gemini: GeminiConfig = field(default_factory=GeminiConfig)
    
    # Resilience
    retry_attempts: int = 3
    retry_delay: float = 1.0
    
    # Feature flags
    enable_caching: bool = True
    cache_ttl_seconds: int = 300  # 5 minutes
    
    @property
    def active_provider(self) -> LLMProvider:
        """
        Determine which provider to use.
        
        Logic:
        1. If provider is explicitly set (not AUTO), use that
        2. If AUTO, prefer Nebius if configured
        3. Fall back to Gemini if Nebius unavailable
        4. Raise error if neither configured
        """
        if self.provider == LLMProvider.NEBIUS:
            if not self.nebius.is_configured:
                raise ValueError("Nebius selected but NEBIUS_API_KEY not set")
            return LLMProvider.NEBIUS
            
        if self.provider == LLMProvider.GEMINI:
            if not self.gemini.is_configured:
                raise ValueError("Gemini selected but GEMINI_API_KEY not set")
            return LLMProvider.GEMINI
        
        # AUTO mode - prefer Nebius
        if self.nebius.is_configured:
            return LLMProvider.NEBIUS
        if self.gemini.is_configured:
            return LLMProvider.GEMINI
            
        raise ValueError(
            "No LLM provider configured. "
            "Set NEBIUS_API_KEY or GEMINI_API_KEY environment variable."
        )
    
    @property
    def is_configured(self) -> bool:
        """Check if at least one provider is configured."""
        return self.nebius.is_configured or self.gemini.is_configured
    
    @classmethod
    def from_env(cls) -> "LLMConfig":
        """
        Create configuration from environment variables.
        
        Environment variables:
            NEBIUS_API_KEY: Nebius Token Factory API key
            NEBIUS_MODEL: Nebius model (default: deepseek-ai/DeepSeek-R1-0528)
            GEMINI_API_KEY: Google Gemini API key (fallback)
            GEMINI_MODEL: Gemini model (default: gemini-2.0-flash)
            LLM_PROVIDER: Force provider (nebius, gemini, auto)
        """
        provider_str = os.getenv("LLM_PROVIDER", "auto").lower()
        provider = LLMProvider(provider_str) if provider_str in ["nebius", "gemini", "auto"] else LLMProvider.AUTO
        
        return cls(
            provider=provider,
            nebius=NebiusConfig(),
            gemini=GeminiConfig(),
        )


# Available Nebius models (Dec 2025)
NEBIUS_MODELS = {
    # Reasoning models (best for metacognition)
    "deepseek-r1": "deepseek-ai/DeepSeek-R1-0528",
    "deepseek-v3": "deepseek-ai/DeepSeek-V3-0324",
    
    # Large context models
    "qwen3-235b": "Qwen/Qwen3-235B-A22B",
    "qwen2.5-72b": "Qwen/Qwen2.5-72B-Instruct",
    "qwen2.5-32b": "Qwen/Qwen2.5-32B-Instruct",
    
    # Fast inference models
    "llama-3.3-70b": "meta-llama/Llama-3.3-70B-Instruct",
    "llama-3.1-70b": "meta-llama/Meta-Llama-3.1-70B-Instruct",
    "llama-3.1-8b": "meta-llama/Meta-Llama-3.1-8B-Instruct",
    
    # Code models
    "qwen2.5-coder": "Qwen/Qwen2.5-Coder-32B-Instruct",
    
    # Multimodal
    "qwen2-vl-72b": "Qwen/Qwen2-VL-72B-Instruct",
}

