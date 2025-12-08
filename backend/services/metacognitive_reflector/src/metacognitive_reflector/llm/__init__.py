"""
Unified LLM Client - Multi-Provider Support
============================================

Supports:
- Nebius AI Studio (OpenAI-compatible API)
- Google Gemini (native API)

Default: Nebius (cost-effective, fast inference)
Fallback: Gemini (when GEMINI_API_KEY is set)

Architecture:
    ┌─────────────────────────────────────────┐
    │          UnifiedLLMClient               │
    │  ┌─────────────┐  ┌─────────────────┐   │
    │  │   Nebius    │  │     Gemini      │   │
    │  │  (Primary)  │  │   (Fallback)    │   │
    │  │ OpenAI API  │  │   Native API    │   │
    │  └─────────────┘  └─────────────────┘   │
    └─────────────────────────────────────────┘

Usage:
    from metacognitive_reflector.llm import get_llm_client
    
    client = get_llm_client()
    response = await client.generate("What is consciousness?")
"""

from .client import (
    UnifiedLLMClient,
    get_llm_client,
    reset_llm_client,
    LLMResponse,
)
from .config import (
    LLMConfig,
    LLMProvider,
    NebiusConfig,
    GeminiConfig,
    NEBIUS_MODELS,
    ModelTier,
    TIER_DEFAULTS,
)

__all__ = [
    # Client
    "UnifiedLLMClient",
    "get_llm_client",
    "reset_llm_client",
    "LLMResponse",
    # Config
    "LLMConfig",
    "LLMProvider",
    "NebiusConfig",
    "GeminiConfig",
    "NEBIUS_MODELS",
    "ModelTier",
    "TIER_DEFAULTS",
]

