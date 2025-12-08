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
    
    # Default model - Llama for fast Language Motor tasks
    model: str = field(
        default_factory=lambda: os.getenv(
            "NEBIUS_MODEL",
            "meta-llama/Llama-3.3-70B-Instruct-fast"
        )
    )
    
    # Reasoning model - DeepSeek-R1 for Tribunal/Judges
    model_reasoning: str = field(
        default_factory=lambda: os.getenv(
            "NEBIUS_MODEL_REASONING",
            "deepseek-ai/DeepSeek-R1-0528-fast"
        )
    )
    
    # Deep analysis model - for complex tasks
    model_deep: str = field(
        default_factory=lambda: os.getenv(
            "NEBIUS_MODEL_DEEP",
            "Qwen/Qwen3-235B-A22B-Thinking-2507"
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
# Benchmarked for Noesis pipeline
NEBIUS_MODELS = {
    # ===== FAST VARIANTS (Optimized for speed) =====
    # Use -fast suffix for production
    "llama-3.3-70b-fast": "meta-llama/Llama-3.3-70B-Instruct-fast",  # 1135ms ⚡
    "deepseek-v3-fast": "deepseek-ai/DeepSeek-V3-0324-fast",          # 1201ms
    "qwen3-32b-fast": "Qwen/Qwen3-32B-fast",                          # 1807ms, 83 tok/s
    "deepseek-r1-fast": "deepseek-ai/DeepSeek-R1-0528-fast",          # 1930ms 🧠
    "gemma-3-27b-fast": "google/gemma-3-27b-it-fast",                 # 2318ms
    
    # ===== REASONING MODELS (Explicit thinking) =====
    "deepseek-r1": "deepseek-ai/DeepSeek-R1-0528",                    # 4516ms
    "qwen3-thinking": "Qwen/Qwen3-30B-A3B-Thinking-2507",             # 3776ms
    "qwen3-235b-thinking": "Qwen/Qwen3-235B-A22B-Thinking-2507",      # Deep analysis
    
    # ===== STANDARD MODELS =====
    "deepseek-v3": "deepseek-ai/DeepSeek-V3-0324",
    "llama-3.3-70b": "meta-llama/Llama-3.3-70B-Instruct",
    "qwen3-32b": "Qwen/Qwen3-32B",
    "gemma-3-27b": "google/gemma-3-27b-it",
    
    # ===== SPECIAL PURPOSE =====
    "qwen3-coder": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
    "qwen2.5-vl": "Qwen/Qwen2.5-VL-72B-Instruct",  # Multimodal
    "hermes-405b": "NousResearch/Hermes-4-405B",   # Large
}

# Model tiers for automatic routing
class ModelTier(str, Enum):
    """Model tiers for task-based routing."""
    FAST = "fast"           # Language Motor, formatting (~1s)
    REASONING = "reasoning"  # Tribunal, judges (~2s)
    DEEP = "deep"           # Complex analysis (~4s+)

TIER_DEFAULTS = {
    ModelTier.FAST: "meta-llama/Llama-3.3-70B-Instruct-fast",
    ModelTier.REASONING: "deepseek-ai/DeepSeek-R1-0528-fast",
    ModelTier.DEEP: "Qwen/Qwen3-235B-A22B-Thinking-2507",
}

