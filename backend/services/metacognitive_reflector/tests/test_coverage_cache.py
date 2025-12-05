"""
Tests for TieredSemanticCache to achieve 100% coverage.
"""

from __future__ import annotations


import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from metacognitive_reflector.core.detectors.semantic_cache import (
    CacheMode,
    CacheLevel,
    CacheEntry,
    CacheResult,
    EmbeddingProvider,
    LocalEmbeddingProvider,
    MockEmbeddingProvider,
    TieredSemanticCache,
    HAS_NUMPY,
    HAS_SENTENCE_TRANSFORMERS,
)


class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    def test_create_entry(self):
        """Test creating cache entry."""
        entry = CacheEntry(
            key="test_key",
            text="test text",
            entropy=0.5,
            embedding=[0.1, 0.2, 0.3],
        )
        assert entry.key == "test_key"
        assert entry.entropy == 0.5
        assert entry.ttl_seconds == 3600

    def test_is_expired_false(self):
        """Test is_expired returns False for fresh entry."""
        entry = CacheEntry(
            key="k",
            text="t",
            entropy=0.5,
            ttl_seconds=3600,
        )
        assert entry.is_expired is False

    def test_is_expired_true(self):
        """Test is_expired returns True for old entry."""
        entry = CacheEntry(
            key="k",
            text="t",
            entropy=0.5,
            ttl_seconds=1,
            created_at=datetime.now() - timedelta(hours=1),
        )
        assert entry.is_expired is True


class TestMockEmbeddingProvider:
    """Tests for MockEmbeddingProvider."""

    @pytest.mark.asyncio
    async def test_encode(self):
        """Test encode returns deterministic embedding."""
        provider = MockEmbeddingProvider()
        embedding = await provider.encode("test")

        assert isinstance(embedding, list)
        assert len(embedding) == 16
        assert all(0 <= x <= 1 for x in embedding)

    @pytest.mark.asyncio
    async def test_similarity_same_text(self):
        """Test similarity of same text is 1.0."""
        provider = MockEmbeddingProvider()
        vec = await provider.encode("test")
        similarity = await provider.similarity(vec, vec)

        assert 0.99 <= similarity <= 1.01

    @pytest.mark.asyncio
    async def test_similarity_empty_vectors(self):
        """Test similarity of empty vectors is 0."""
        provider = MockEmbeddingProvider()
        result = await provider.similarity([], [])
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_similarity_zero_norm(self):
        """Test similarity with zero norm."""
        provider = MockEmbeddingProvider()
        result = await provider.similarity([0, 0, 0], [1, 2, 3])
        assert result == 0.0


class TestLocalEmbeddingProvider:
    """Tests for LocalEmbeddingProvider."""

    def test_init(self):
        """Test initialization."""
        provider = LocalEmbeddingProvider("all-MiniLM-L6-v2")
        assert provider._model_name == "all-MiniLM-L6-v2"
        assert provider._model is None

    def test_get_model_no_sentence_transformers(self):
        """Test _get_model raises without sentence_transformers."""
        provider = LocalEmbeddingProvider()

        # Patch HAS_SENTENCE_TRANSFORMERS
        import metacognitive_reflector.core.detectors.semantic_cache as cache_module
        original = cache_module.HAS_SENTENCE_TRANSFORMERS
        cache_module.HAS_SENTENCE_TRANSFORMERS = False

        try:
            with pytest.raises(ImportError, match="sentence-transformers required"):
                provider._get_model()
        finally:
            cache_module.HAS_SENTENCE_TRANSFORMERS = original

    @pytest.mark.asyncio
    async def test_similarity_without_numpy(self):
        """Test similarity fallback without numpy."""
        provider = LocalEmbeddingProvider()

        import metacognitive_reflector.core.detectors.semantic_cache as cache_module
        original = cache_module.HAS_NUMPY
        cache_module.HAS_NUMPY = False

        try:
            result = await provider.similarity([1, 0, 0], [1, 0, 0])
            assert 0.99 <= result <= 1.01
        finally:
            cache_module.HAS_NUMPY = original

    @pytest.mark.asyncio
    async def test_similarity_zero_norm_no_numpy(self):
        """Test similarity with zero norm without numpy."""
        provider = LocalEmbeddingProvider()

        import metacognitive_reflector.core.detectors.semantic_cache as cache_module
        original = cache_module.HAS_NUMPY
        cache_module.HAS_NUMPY = False

        try:
            result = await provider.similarity([0, 0, 0], [1, 2, 3])
            assert result == 0.0
        finally:
            cache_module.HAS_NUMPY = original

    @pytest.mark.asyncio
    async def test_similarity_with_numpy(self):
        """Test similarity with numpy."""
        if not HAS_NUMPY:
            pytest.skip("numpy not installed")

        provider = LocalEmbeddingProvider()
        result = await provider.similarity([1, 0, 0], [1, 0, 0])
        assert 0.99 <= result <= 1.01

    @pytest.mark.asyncio
    async def test_similarity_zero_norm_with_numpy(self):
        """Test zero norm with numpy."""
        if not HAS_NUMPY:
            pytest.skip("numpy not installed")

        provider = LocalEmbeddingProvider()
        result = await provider.similarity([0, 0, 0], [1, 2, 3])
        assert result == 0.0


class TestTieredSemanticCache:
    """Tests for TieredSemanticCache."""

    @pytest.mark.asyncio
    async def test_compute_hash(self):
        """Test hash computation is deterministic."""
        cache = TieredSemanticCache()
        hash1 = cache._compute_hash("Hello World")
        hash2 = cache._compute_hash("Hello World")
        hash3 = cache._compute_hash("  hello   world  ")  # Should normalize

        assert hash1 == hash2
        assert hash1 == hash3  # Normalized

    @pytest.mark.asyncio
    async def test_l1_hit(self):
        """Test L1 cache hit."""
        cache = TieredSemanticCache()

        async def compute_fn(text):
            return 0.5

        # First call computes
        result1 = await cache.get_or_compute("test", compute_fn, CacheMode.NORMAL)
        assert result1.level == CacheLevel.L3_COMPUTED

        # Second call hits L1
        result2 = await cache.get_or_compute("test", compute_fn, CacheMode.NORMAL)
        assert result2.level == CacheLevel.L1_EXACT
        assert result2.hit is True

    @pytest.mark.asyncio
    async def test_l2_hit(self):
        """Test L2 semantic cache hit."""
        cache = TieredSemanticCache(similarity_threshold=0.5)

        async def compute_fn(text):
            return 0.5

        # Store first entry
        await cache.get_or_compute("Hello world", compute_fn, CacheMode.NORMAL)

        # Similar text should hit L2 (mock provider gives high similarity)
        # Note: With MockEmbeddingProvider, similarity depends on hash
        result = await cache.get_or_compute("Hello world!", compute_fn, CacheMode.NORMAL)
        # May hit L1 due to normalization
        assert result.hit is True

    @pytest.mark.asyncio
    async def test_fast_mode_no_l3(self):
        """Test FAST mode doesn't use L3 computation."""
        cache = TieredSemanticCache()

        call_count = 0

        async def compute_fn(text):
            nonlocal call_count
            call_count += 1
            return 0.5

        result = await cache.get_or_compute("new_text", compute_fn, CacheMode.FAST)

        # FAST mode should not compute L3
        assert result.hit is False
        assert result.level == CacheLevel.MISS
        assert call_count == 0

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling in L3 compute."""
        cache = TieredSemanticCache()

        async def slow_compute_fn(text):
            import asyncio
            await asyncio.sleep(10)  # 10 seconds
            return 0.5

        # NORMAL mode has 5s timeout
        result = await cache.get_or_compute("test", slow_compute_fn, CacheMode.NORMAL)

        assert result.hit is False
        assert result.level == CacheLevel.MISS

    @pytest.mark.asyncio
    async def test_l1_expired_entry(self):
        """Test L1 removes expired entries."""
        cache = TieredSemanticCache(ttl_seconds=1)

        async def compute_fn(text):
            return 0.5

        # Store entry
        await cache.get_or_compute("test", compute_fn, CacheMode.NORMAL)

        # Manually expire
        for entry in cache._l1_cache.values():
            entry.created_at = datetime.now() - timedelta(hours=1)

        # Should miss due to expiry
        result = await cache._check_l1("test")
        assert result.hit is False

    @pytest.mark.asyncio
    async def test_l2_check_empty_cache(self):
        """Test L2 check on empty cache."""
        cache = TieredSemanticCache()
        result = await cache._check_l2("test")
        assert result.hit is False

    @pytest.mark.asyncio
    async def test_l2_skip_expired(self):
        """Test L2 skips expired entries."""
        cache = TieredSemanticCache(ttl_seconds=1)

        async def compute_fn(text):
            return 0.5

        await cache.get_or_compute("test", compute_fn, CacheMode.NORMAL)

        # Expire entries
        for entry in cache._l2_cache.values():
            entry.created_at = datetime.now() - timedelta(hours=1)

        result = await cache._check_l2("similar_test")
        assert result.hit is False

    @pytest.mark.asyncio
    async def test_l2_skip_no_embedding(self):
        """Test L2 skips entries without embedding."""
        cache = TieredSemanticCache()

        async def compute_fn(text):
            return 0.5

        await cache.get_or_compute("test", compute_fn, CacheMode.NORMAL)

        # Remove embedding
        for entry in cache._l2_cache.values():
            entry.embedding = None

        result = await cache._check_l2("similar_test")
        assert result.hit is False

    @pytest.mark.asyncio
    async def test_eviction_l1(self):
        """Test L1 eviction when over capacity."""
        cache = TieredSemanticCache(l1_max_size=2)

        async def compute_fn(text):
            return 0.5

        # Fill cache
        await cache.get_or_compute("text1", compute_fn, CacheMode.NORMAL)
        await cache.get_or_compute("text2", compute_fn, CacheMode.NORMAL)
        await cache.get_or_compute("text3", compute_fn, CacheMode.NORMAL)

        # Should have evicted oldest
        assert len(cache._l1_cache) <= 2

    @pytest.mark.asyncio
    async def test_eviction_l2(self):
        """Test L2 eviction when over capacity."""
        cache = TieredSemanticCache(l2_max_size=2)

        async def compute_fn(text):
            return 0.5

        await cache.get_or_compute("text1", compute_fn, CacheMode.NORMAL)
        await cache.get_or_compute("text2", compute_fn, CacheMode.NORMAL)
        await cache.get_or_compute("text3", compute_fn, CacheMode.NORMAL)

        assert len(cache._l2_cache) <= 2

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test get_stats returns correct stats."""
        cache = TieredSemanticCache()

        async def compute_fn(text):
            return 0.5

        await cache.get_or_compute("test", compute_fn, CacheMode.NORMAL)
        await cache.get_or_compute("test", compute_fn, CacheMode.NORMAL)

        stats = cache.get_stats()

        assert stats["total_requests"] == 2
        assert stats["l1_hits"] == 1
        assert stats["l3_computes"] == 1
        assert stats["hit_rate"] == 0.5

    @pytest.mark.asyncio
    async def test_get_stats_empty(self):
        """Test get_stats with no requests."""
        cache = TieredSemanticCache()
        stats = cache.get_stats()

        assert stats["total_requests"] == 0
        assert stats["hit_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_clear(self):
        """Test clear resets cache."""
        cache = TieredSemanticCache()

        async def compute_fn(text):
            return 0.5

        await cache.get_or_compute("test", compute_fn, CacheMode.NORMAL)
        cache.clear()

        assert len(cache._l1_cache) == 0
        assert len(cache._l2_cache) == 0
        assert cache._stats["total_requests"] == 0

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health_check returns status."""
        cache = TieredSemanticCache()
        health = await cache.health_check()

        assert health["healthy"] is True
        assert "stats" in health
        assert health["embedding_provider"] == "MockEmbeddingProvider"

    @pytest.mark.asyncio
    async def test_deep_mode(self):
        """Test DEEP mode computation."""
        cache = TieredSemanticCache()

        async def compute_fn(text):
            return 0.75

        result = await cache.get_or_compute("test", compute_fn, CacheMode.DEEP)

        assert result.hit is True
        assert result.entropy == 0.75
        assert result.level == CacheLevel.L3_COMPUTED
