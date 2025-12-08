"""
Unified LLM Client - Multi-Provider Support
============================================

Provides a unified interface for LLM inference across providers:
- Nebius Token Factory (OpenAI-compatible)
- Google Gemini (native API)

Reference:
- Nebius: https://docs.tokenfactory.nebius.com/quickstart
- Cookbook: https://github.com/nebius/token-factory-cookbook

Usage:
    client = get_llm_client()
    response = await client.generate("What is consciousness?")
    
    # Or with chat format
    response = await client.chat([
        {"role": "system", "content": "You are a metacognitive judge."},
        {"role": "user", "content": "Evaluate this action..."}
    ])
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

import httpx

from .config import LLMConfig, LLMProvider, NebiusConfig, GeminiConfig

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """
    Unified response from LLM.
    
    Attributes:
        text: Generated text content
        model: Model used for generation
        provider: Provider used (nebius/gemini)
        usage: Token usage statistics
        finish_reason: Why generation stopped
        latency_ms: Request latency in milliseconds
        cached: Whether response was from cache
        raw: Raw response from provider
    """
    text: str
    model: str
    provider: LLMProvider
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"
    latency_ms: float = 0.0
    cached: bool = False
    raw: Optional[Dict[str, Any]] = None
    
    @property
    def input_tokens(self) -> int:
        """Number of input tokens."""
        return self.usage.get("prompt_tokens", 0)
    
    @property
    def output_tokens(self) -> int:
        """Number of output tokens."""
        return self.usage.get("completion_tokens", 0)
    
    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return self.usage.get("total_tokens", 0)


class UnifiedLLMClient:
    """
    Unified LLM Client with multi-provider support.
    
    Features:
    - OpenAI-compatible API for Nebius
    - Native API for Gemini
    - Response caching (5min TTL)
    - Automatic retries with exponential backoff
    - Provider fallback
    
    Example:
        client = UnifiedLLMClient()
        
        # Simple generation
        response = await client.generate("What is truth?")
        print(response.text)
        
        # Chat format
        response = await client.chat([
            {"role": "system", "content": "You are VERITAS."},
            {"role": "user", "content": "Evaluate this claim..."}
        ])
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize the unified LLM client.
        
        Args:
            config: LLM configuration (loads from env if not provided)
        """
        self.config = config or LLMConfig.from_env()
        
        # Response cache
        self._cache: Dict[str, tuple[LLMResponse, float]] = {}
        
        # Statistics
        self._total_requests = 0
        self._total_tokens = 0
        self._cache_hits = 0
        
        # Log initialization
        provider = self.config.active_provider
        if provider == LLMProvider.NEBIUS:
            model = self.config.nebius.model
        else:
            model = self.config.gemini.model
            
        logger.info(
            f"🧠 LLM Client initialized | "
            f"Provider: {provider.value} | "
            f"Model: {model}"
        )
    
    async def generate(
        self,
        prompt: str,
        *,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        use_cache: bool = True,
    ) -> LLMResponse:
        """
        Generate text from a prompt.
        
        Args:
            prompt: The user prompt
            system_instruction: Optional system message
            temperature: Override temperature
            max_tokens: Override max tokens
            use_cache: Whether to use response cache
            
        Returns:
            LLMResponse with generated text
        """
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        
        return await self.chat(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            use_cache=use_cache,
        )
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        use_cache: bool = True,
    ) -> LLMResponse:
        """
        Generate response from chat messages.
        
        Args:
            messages: List of chat messages [{"role": "...", "content": "..."}]
            temperature: Override temperature
            max_tokens: Override max tokens
            use_cache: Whether to use response cache
            
        Returns:
            LLMResponse with generated text
        """
        # Check cache
        if use_cache and self.config.enable_caching:
            cache_key = self._cache_key(messages, temperature, max_tokens)
            cached = self._get_cached(cache_key)
            if cached:
                self._cache_hits += 1
                return cached
        
        # Route to appropriate provider
        provider = self.config.active_provider
        
        for attempt in range(self.config.retry_attempts):
            try:
                if provider == LLMProvider.NEBIUS:
                    response = await self._nebius_chat(
                        messages, temperature, max_tokens
                    )
                else:
                    response = await self._gemini_chat(
                        messages, temperature, max_tokens
                    )
                
                # Cache response
                if use_cache and self.config.enable_caching:
                    self._cache[cache_key] = (response, time.time())
                
                # Update stats
                self._total_requests += 1
                self._total_tokens += response.total_tokens
                
                return response
                
            except Exception as e:
                logger.warning(
                    f"LLM request failed (attempt {attempt + 1}): {e}"
                )
                if attempt < self.config.retry_attempts - 1:
                    delay = self.config.retry_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                else:
                    raise
        
        # Should not reach here
        raise RuntimeError("All retry attempts failed")
    
    async def _nebius_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float],
        max_tokens: Optional[int],
    ) -> LLMResponse:
        """
        Send chat request to Nebius Token Factory.
        
        Uses OpenAI-compatible API.
        Reference: https://docs.tokenfactory.nebius.com/quickstart
        """
        config = self.config.nebius
        
        # Build request body (OpenAI format)
        request_body = {
            "model": config.model,
            "messages": messages,
            "temperature": temperature or config.temperature,
            "max_tokens": max_tokens or config.max_tokens,
        }
        
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            response = await client.post(
                f"{config.base_url}chat/completions",
                json=request_body,
                headers={
                    "Authorization": f"Bearer {config.api_key}",
                    "Content-Type": "application/json",
                },
            )
            
            if response.status_code != 200:
                error_text = response.text
                raise RuntimeError(
                    f"Nebius API error {response.status_code}: {error_text}"
                )
            
            result = response.json()
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Parse OpenAI-format response
        choice = result.get("choices", [{}])[0]
        message = choice.get("message", {})
        
        return LLMResponse(
            text=message.get("content", ""),
            model=result.get("model", config.model),
            provider=LLMProvider.NEBIUS,
            usage=result.get("usage", {}),
            finish_reason=choice.get("finish_reason", "stop"),
            latency_ms=latency_ms,
            cached=False,
            raw=result,
        )
    
    async def _gemini_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float],
        max_tokens: Optional[int],
    ) -> LLMResponse:
        """
        Send chat request to Google Gemini.
        
        Uses native Gemini API format.
        """
        config = self.config.gemini
        
        # Convert messages to Gemini format
        contents = []
        system_instruction = None
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                system_instruction = content
            else:
                gemini_role = "user" if role == "user" else "model"
                contents.append({
                    "role": gemini_role,
                    "parts": [{"text": content}]
                })
        
        # Build request
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/"
            f"models/{config.model}:generateContent"
        )
        
        request_body: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature or config.temperature,
                "maxOutputTokens": max_tokens or config.max_tokens,
            }
        }
        
        if system_instruction:
            # Add temporal grounding
            current_time = datetime.now().strftime("%A, %d %B %Y, %H:%M")
            grounded_instruction = (
                f"Current date: {current_time}.\n\n{system_instruction}"
            )
            request_body["systemInstruction"] = {
                "parts": [{"text": grounded_instruction}]
            }
        
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            response = await client.post(
                url,
                params={"key": config.api_key},
                json=request_body,
                headers={"Content-Type": "application/json"},
            )
            
            if response.status_code != 200:
                error_text = response.text
                raise RuntimeError(
                    f"Gemini API error {response.status_code}: {error_text}"
                )
            
            result = response.json()
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Parse Gemini response
        candidates = result.get("candidates", [{}])
        content = candidates[0].get("content", {}) if candidates else {}
        parts = content.get("parts", [{}])
        text = parts[0].get("text", "") if parts else ""
        
        # Extract usage
        usage_metadata = result.get("usageMetadata", {})
        usage = {
            "prompt_tokens": usage_metadata.get("promptTokenCount", 0),
            "completion_tokens": usage_metadata.get("candidatesTokenCount", 0),
            "total_tokens": usage_metadata.get("totalTokenCount", 0),
        }
        
        return LLMResponse(
            text=text,
            model=config.model,
            provider=LLMProvider.GEMINI,
            usage=usage,
            finish_reason=candidates[0].get("finishReason", "STOP") if candidates else "STOP",
            latency_ms=latency_ms,
            cached=False,
            raw=result,
        )
    
    def _cache_key(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float],
        max_tokens: Optional[int],
    ) -> str:
        """Generate cache key from request parameters."""
        provider = self.config.active_provider
        if provider == LLMProvider.NEBIUS:
            model = self.config.nebius.model
        else:
            model = self.config.gemini.model
        
        key_data = {
            "provider": provider.value,
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]
    
    def _get_cached(self, key: str) -> Optional[LLMResponse]:
        """Get cached response if not expired."""
        if key not in self._cache:
            return None
        
        response, timestamp = self._cache[key]
        if time.time() - timestamp > self.config.cache_ttl_seconds:
            del self._cache[key]
            return None
        
        # Return copy with cached flag
        return LLMResponse(
            text=response.text,
            model=response.model,
            provider=response.provider,
            usage=response.usage,
            finish_reason=response.finish_reason,
            latency_ms=0.0,
            cached=True,
            raw=response.raw,
        )
    
    def clear_cache(self) -> int:
        """Clear response cache. Returns number of entries cleared."""
        count = len(self._cache)
        self._cache.clear()
        return count
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            "provider": self.config.active_provider.value,
            "total_requests": self._total_requests,
            "total_tokens": self._total_tokens,
            "cache_hits": self._cache_hits,
            "cache_size": len(self._cache),
            "cache_hit_rate": (
                self._cache_hits / max(1, self._total_requests + self._cache_hits)
            ),
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check LLM connectivity.
        
        Returns:
            Dict with health status and provider info
        """
        try:
            response = await self.generate(
                "Say 'OK' if you're operational.",
                max_tokens=10,
                use_cache=False,
            )
            return {
                "healthy": True,
                "provider": response.provider.value,
                "model": response.model,
                "latency_ms": response.latency_ms,
                "response": response.text[:50],
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "provider": self.config.active_provider.value,
            }


# Singleton instance
_client_instance: Optional[UnifiedLLMClient] = None


def get_llm_client(config: Optional[LLMConfig] = None) -> UnifiedLLMClient:
    """
    Get or create the LLM client singleton.
    
    Args:
        config: Optional configuration (uses env vars if not provided)
        
    Returns:
        UnifiedLLMClient instance
    """
    global _client_instance
    
    if _client_instance is None or config is not None:
        _client_instance = UnifiedLLMClient(config)
    
    return _client_instance


def reset_llm_client() -> None:
    """Reset the LLM client singleton (useful for testing)."""
    global _client_instance
    _client_instance = None

