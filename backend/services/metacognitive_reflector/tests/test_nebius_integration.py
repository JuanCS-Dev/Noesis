"""
Nebius Token Factory Integration Tests
======================================

Tests for the unified LLM client with Nebius support.

Run:
    pytest tests/test_nebius_integration.py -v
    
Or standalone:
    python tests/test_nebius_integration.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import pytest


class TestNebiusConfig:
    """Test Nebius configuration."""
    
    def test_config_from_env(self):
        """Test configuration loads from environment."""
        from metacognitive_reflector.llm import LLMConfig, LLMProvider
        
        config = LLMConfig.from_env()
        
        # Should have valid structure
        assert config.nebius is not None
        assert config.gemini is not None
        assert config.retry_attempts >= 1
    
    def test_nebius_config_defaults(self):
        """Test Nebius default configuration."""
        from metacognitive_reflector.llm import NebiusConfig
        
        config = NebiusConfig()
        
        assert config.base_url == "https://api.tokenfactory.nebius.com/v1/"
        assert "DeepSeek" in config.model or "deepseek" in config.model
        assert config.max_tokens > 0
        assert config.timeout > 0
    
    def test_provider_auto_selection(self):
        """Test automatic provider selection."""
        from metacognitive_reflector.llm import LLMConfig, LLMProvider
        
        config = LLMConfig.from_env()
        
        # If NEBIUS_API_KEY is set, should select Nebius
        if os.getenv("NEBIUS_API_KEY"):
            assert config.active_provider == LLMProvider.NEBIUS
        elif os.getenv("GEMINI_API_KEY"):
            assert config.active_provider == LLMProvider.GEMINI


class TestUnifiedLLMClient:
    """Test the unified LLM client."""
    
    def test_client_initialization(self):
        """Test client initializes correctly."""
        from metacognitive_reflector.llm import get_llm_client, reset_llm_client
        
        reset_llm_client()
        
        # Should not raise if at least one provider is configured
        if os.getenv("NEBIUS_API_KEY") or os.getenv("GEMINI_API_KEY"):
            client = get_llm_client()
            assert client is not None
            assert client.config is not None
    
    def test_client_singleton(self):
        """Test client is singleton."""
        from metacognitive_reflector.llm import get_llm_client, reset_llm_client
        
        reset_llm_client()
        
        if os.getenv("NEBIUS_API_KEY") or os.getenv("GEMINI_API_KEY"):
            client1 = get_llm_client()
            client2 = get_llm_client()
            assert client1 is client2
    
    @pytest.mark.asyncio
    async def test_nebius_generation(self):
        """Test text generation with Nebius."""
        from metacognitive_reflector.llm import get_llm_client, LLMProvider
        
        if not os.getenv("NEBIUS_API_KEY"):
            pytest.skip("NEBIUS_API_KEY not set")
        
        client = get_llm_client()
        
        response = await client.generate(
            "Say 'Hello from Nebius' and nothing else.",
            max_tokens=50,
            use_cache=False,
        )
        
        assert response.text
        assert response.provider == LLMProvider.NEBIUS
        assert response.latency_ms > 0
        assert response.total_tokens > 0
        print(f"✓ Nebius response: {response.text[:100]}")
        print(f"✓ Latency: {response.latency_ms:.0f}ms")
        print(f"✓ Tokens: {response.total_tokens}")
    
    @pytest.mark.asyncio
    async def test_nebius_chat(self):
        """Test chat format with Nebius."""
        from metacognitive_reflector.llm import get_llm_client
        
        if not os.getenv("NEBIUS_API_KEY"):
            pytest.skip("NEBIUS_API_KEY not set")
        
        client = get_llm_client()
        
        response = await client.chat([
            {"role": "system", "content": "You are a metacognitive judge named VERITAS."},
            {"role": "user", "content": "What is your purpose? Answer in one sentence."},
        ], max_tokens=100)
        
        assert response.text
        assert len(response.text) > 10
        print(f"✓ Chat response: {response.text[:200]}")
    
    @pytest.mark.asyncio
    async def test_response_caching(self):
        """Test response caching works."""
        from metacognitive_reflector.llm import get_llm_client, reset_llm_client
        
        if not os.getenv("NEBIUS_API_KEY"):
            pytest.skip("NEBIUS_API_KEY not set")
        
        reset_llm_client()
        client = get_llm_client()
        
        prompt = "What is 2 + 2? Answer with just the number."
        
        # First call - not cached
        response1 = await client.generate(prompt, max_tokens=10)
        assert not response1.cached
        
        # Second call - should be cached
        response2 = await client.generate(prompt, max_tokens=10)
        assert response2.cached
        assert response2.latency_ms == 0.0
        assert response2.text == response1.text
        
        print(f"✓ Cache working: hit_rate={client.stats['cache_hit_rate']:.1%}")
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check endpoint."""
        from metacognitive_reflector.llm import get_llm_client
        
        if not os.getenv("NEBIUS_API_KEY"):
            pytest.skip("NEBIUS_API_KEY not set")
        
        client = get_llm_client()
        
        health = await client.health_check()
        
        assert "healthy" in health
        print(f"✓ Health check: {health}")


class TestMetacognitiveIntegration:
    """Test integration with metacognitive pipeline."""
    
    @pytest.mark.asyncio
    async def test_tribunal_reasoning(self):
        """Test reasoning capability for tribunal evaluation."""
        from metacognitive_reflector.llm import get_llm_client
        
        if not os.getenv("NEBIUS_API_KEY"):
            pytest.skip("NEBIUS_API_KEY not set")
        
        client = get_llm_client()
        
        # Simulate a tribunal evaluation prompt
        response = await client.chat([
            {
                "role": "system",
                "content": (
                    "You are VERITAS, a metacognitive judge that evaluates truth. "
                    "Your purpose is to detect deception, hallucination, and misrepresentation. "
                    "Analyze claims with epistemic rigor."
                )
            },
            {
                "role": "user",
                "content": (
                    "Evaluate this claim for truthfulness:\n"
                    "\"The Earth is flat and NASA is hiding the truth.\"\n\n"
                    "Provide:\n"
                    "1. Verdict (TRUE/FALSE/UNCERTAIN)\n"
                    "2. Confidence (0.0-1.0)\n"
                    "3. Brief reasoning"
                )
            }
        ], max_tokens=500, temperature=0.3)
        
        assert response.text
        assert "FALSE" in response.text.upper() or "UNCERTAIN" in response.text.upper()
        print(f"✓ Tribunal reasoning:\n{response.text[:500]}")


async def run_quick_test():
    """Run a quick integration test."""
    from metacognitive_reflector.llm import get_llm_client, reset_llm_client
    
    print("\n" + "=" * 60)
    print("🧠 NEBIUS TOKEN FACTORY - QUICK TEST")
    print("=" * 60)
    
    if not os.getenv("NEBIUS_API_KEY"):
        print("❌ NEBIUS_API_KEY not set in environment")
        print("   Set it in .env or export NEBIUS_API_KEY=...")
        return False
    
    reset_llm_client()
    client = get_llm_client()
    
    print(f"\n📡 Provider: {client.config.active_provider.value}")
    print(f"🤖 Model: {client.config.nebius.model}")
    print(f"🔗 URL: {client.config.nebius.base_url}")
    
    print("\n⏳ Testing connection...")
    
    try:
        response = await client.generate(
            "Say 'Noesis is alive!' and nothing else.",
            max_tokens=20,
            use_cache=False,
        )
        
        print(f"\n✅ SUCCESS!")
        print(f"   Response: {response.text}")
        print(f"   Latency: {response.latency_ms:.0f}ms")
        print(f"   Tokens: {response.total_tokens}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        return False


if __name__ == "__main__":
    # Load .env if exists
    env_path = Path(__file__).parent.parent.parent.parent.parent.parent / ".env"
    if env_path.exists():
        print(f"Loading .env from {env_path}")
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value
    
    # Run quick test
    success = asyncio.run(run_quick_test())
    sys.exit(0 if success else 1)

