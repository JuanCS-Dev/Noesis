"""
MAXIMUS 2.0 - TieredSemanticCache
=================================

Three-tier semantic cache for VERITAS entropy computation:
- L1: Exact hash match (<1ms)
- L2: Semantic similarity via embeddings (~50ms)
- L3: Full entropy computation (5-15s)

Operation Modes:
- FAST: L1 + L2 only, timeout 500ms
- NORMAL: L1 + L2 + L3 (3 samples), timeout 5s
- DEEP: L1 + L2 + L3 (10 samples), timeout 30s

Based on GPTCache (100x speedup) and Portkey (20% hit rate @ 99% accuracy).
Flow: Request → Hash → L1 → (miss) → L2 → (miss) → L3 Compute
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False


class CacheMode(str, Enum):
    """Operation modes for tiered cache."""
    FAST = "fast"       # L1 + L2 only, timeout 500ms
    NORMAL = "normal"   # L1 + L2 + L3 (3 samples), timeout 5s
    DEEP = "deep"       # L1 + L2 + L3 (10 samples), timeout 30s


class CacheLevel(str, Enum):
    """Cache tier that served the request."""
    L1_EXACT = "L1_exact"
    L2_SEMANTIC = "L2_semantic"
    L3_COMPUTED = "L3_computed"
    MISS = "miss"


@dataclass
class CacheEntry:  # pylint: disable=too-many-instance-attributes
    """Entry in the semantic cache."""
    key: str
    text: str
    entropy: float
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    ttl_seconds: int = 3600  # 1 hour default

    @property
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        age = (datetime.now() - self.created_at).total_seconds()
        return age > self.ttl_seconds


@dataclass
class CacheResult:
    """Result from cache lookup."""
    hit: bool
    level: CacheLevel
    entropy: Optional[float]
    latency_ms: float
    confidence: float = 1.0  # Lower for L2 semantic matches


class EmbeddingProvider(ABC):
    """Abstract embedding provider for L2 cache."""

    @abstractmethod
    async def encode(self, text: str) -> List[float]:
        """Encode text to embedding vector."""

    @abstractmethod
    async def similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between vectors."""


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local sentence-transformers embedding provider."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize with sentence-transformers model."""
        self._model_name = model_name
        self._model: Optional[Any] = None

    def _get_model(self) -> Any:
        """Lazy load the model."""
        if self._model is None:
            if not HAS_SENTENCE_TRANSFORMERS:
                raise ImportError(
                    "sentence-transformers required for LocalEmbeddingProvider. "
                    "Install with: pip install sentence-transformers"
                )
            self._model = SentenceTransformer(self._model_name)
        return self._model

    async def encode(self, text: str) -> List[float]:
        """Encode text using sentence-transformers."""
        model = self._get_model()
        # Run in thread to avoid blocking
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: model.encode(text, convert_to_numpy=True)
        )
        return embedding.tolist()

    async def similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity."""
        if not HAS_NUMPY:
            # Fallback to pure Python
            dot = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = sum(a * a for a in vec1) ** 0.5
            norm2 = sum(b * b for b in vec2) ** 0.5
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return dot / (norm1 * norm2)

        arr1 = np.array(vec1)
        arr2 = np.array(vec2)
        dot = np.dot(arr1, arr2)
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(dot / (norm1 * norm2))


class MockEmbeddingProvider(EmbeddingProvider):
    """Mock embedding provider for testing."""

    async def encode(self, text: str) -> List[float]:
        """Return hash-based mock embedding."""
        h = hashlib.md5(text.encode()).hexdigest()
        return [int(c, 16) / 15.0 for c in h[:16]]

    async def similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity."""
        if not vec1 or not vec2:
            return 0.0
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)


class TieredSemanticCache:  # pylint: disable=too-many-instance-attributes
    """
    Three-tier semantic cache for entropy computation.

    L1: In-memory exact hash match
    L2: Semantic similarity via embeddings
    L3: Full computation (delegated to entropy detector)

    Usage:
        cache = TieredSemanticCache()
        result = await cache.get_or_compute(
            text="The capital of France is Paris",
            compute_fn=entropy_detector.compute_entropy,
            mode=CacheMode.NORMAL
        )
    """

    # Mode configurations
    MODE_CONFIG: Dict[CacheMode, Dict[str, Any]] = {
        CacheMode.FAST: {
            "timeout_ms": 500,
            "use_l3": False,
            "l3_samples": 0,
        },
        CacheMode.NORMAL: {
            "timeout_ms": 5000,
            "use_l3": True,
            "l3_samples": 3,
        },
        CacheMode.DEEP: {
            "timeout_ms": 30000,
            "use_l3": True,
            "l3_samples": 10,
        },
    }

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        embedding_provider: Optional[EmbeddingProvider] = None,
        l1_max_size: int = 1000,
        l2_max_size: int = 5000,
        similarity_threshold: float = 0.92,
        ttl_seconds: int = 3600,
    ):
        """
        Initialize tiered cache.

        Args:
            embedding_provider: Provider for L2 semantic matching
            l1_max_size: Maximum entries in L1 cache
            l2_max_size: Maximum entries in L2 cache
            similarity_threshold: Minimum similarity for L2 match
            ttl_seconds: Time-to-live for cache entries
        """
        self._embedding_provider = embedding_provider or MockEmbeddingProvider()
        self._l1_max_size = l1_max_size
        self._l2_max_size = l2_max_size
        self._similarity_threshold = similarity_threshold
        self._ttl_seconds = ttl_seconds

        # L1: Hash-keyed exact match cache
        self._l1_cache: Dict[str, CacheEntry] = {}

        # L2: Semantic similarity cache (stores embeddings)
        self._l2_cache: Dict[str, CacheEntry] = {}

        # Statistics
        self._stats = {
            "l1_hits": 0,
            "l2_hits": 0,
            "l3_computes": 0,
            "misses": 0,
            "total_requests": 0,
        }

    def _compute_hash(self, text: str) -> str:
        """Compute deterministic hash for text."""
        normalized = " ".join(text.lower().split())
        return hashlib.sha256(normalized.encode()).hexdigest()

    async def get_or_compute(
        self,
        text: str,
        compute_fn: Any,
        mode: CacheMode = CacheMode.NORMAL,
    ) -> CacheResult:
        """
        Get entropy from cache or compute it.

        Args:
            text: Text to compute entropy for
            compute_fn: Async function to compute entropy
            mode: Operation mode (FAST, NORMAL, DEEP)

        Returns:
            CacheResult with entropy and cache level
        """
        self._stats["total_requests"] += 1
        start_time = time.time()
        config = self.MODE_CONFIG[mode]

        # L1: Exact hash match
        l1_result = await self._check_l1(text)
        if l1_result.hit:
            return l1_result

        # L2: Semantic similarity match
        l2_result = await self._check_l2(text)
        if l2_result.hit:
            return l2_result

        # L3: Full computation (if allowed by mode)
        if not config["use_l3"]:
            self._stats["misses"] += 1
            latency = (time.time() - start_time) * 1000
            return CacheResult(
                hit=False,
                level=CacheLevel.MISS,
                entropy=None,
                latency_ms=latency,
                confidence=0.0,
            )

        # Compute with timeout
        timeout_s = config["timeout_ms"] / 1000
        try:
            entropy = await asyncio.wait_for(
                compute_fn(text),
                timeout=timeout_s
            )

            # Store in both caches
            await self._store(text, entropy)

            self._stats["l3_computes"] += 1
            latency = (time.time() - start_time) * 1000

            return CacheResult(
                hit=True,
                level=CacheLevel.L3_COMPUTED,
                entropy=entropy,
                latency_ms=latency,
                confidence=1.0,
            )

        except asyncio.TimeoutError:
            self._stats["misses"] += 1
            latency = (time.time() - start_time) * 1000
            return CacheResult(
                hit=False,
                level=CacheLevel.MISS,
                entropy=None,
                latency_ms=latency,
                confidence=0.0,
            )

    async def _check_l1(self, text: str) -> CacheResult:
        """Check L1 exact match cache."""
        start = time.time()
        key = self._compute_hash(text)

        if key in self._l1_cache:
            entry = self._l1_cache[key]
            if not entry.is_expired:
                entry.access_count += 1
                entry.last_accessed = datetime.now()
                self._stats["l1_hits"] += 1

                return CacheResult(
                    hit=True,
                    level=CacheLevel.L1_EXACT,
                    entropy=entry.entropy,
                    latency_ms=(time.time() - start) * 1000,
                    confidence=1.0,
                )
            # Remove expired entry
            del self._l1_cache[key]

        return CacheResult(
            hit=False,
            level=CacheLevel.MISS,
            entropy=None,
            latency_ms=(time.time() - start) * 1000,
        )

    async def _check_l2(self, text: str) -> CacheResult:
        """Check L2 semantic similarity cache."""
        start = time.time()

        if not self._l2_cache:
            return CacheResult(
                hit=False,
                level=CacheLevel.MISS,
                entropy=None,
                latency_ms=(time.time() - start) * 1000,
            )

        # Encode query text
        query_embedding = await self._embedding_provider.encode(text)

        # Find most similar entry
        best_similarity = 0.0
        best_entry: Optional[CacheEntry] = None

        for entry in self._l2_cache.values():
            if entry.is_expired:
                continue
            if entry.embedding is None:
                continue

            similarity = await self._embedding_provider.similarity(
                query_embedding, entry.embedding
            )

            if similarity > best_similarity:
                best_similarity = similarity
                best_entry = entry

        # Check threshold
        if best_entry and best_similarity >= self._similarity_threshold:
            best_entry.access_count += 1
            best_entry.last_accessed = datetime.now()
            self._stats["l2_hits"] += 1

            return CacheResult(
                hit=True,
                level=CacheLevel.L2_SEMANTIC,
                entropy=best_entry.entropy,
                latency_ms=(time.time() - start) * 1000,
                confidence=best_similarity,  # Confidence = similarity
            )

        return CacheResult(
            hit=False,
            level=CacheLevel.MISS,
            entropy=None,
            latency_ms=(time.time() - start) * 1000,
        )

    async def _store(self, text: str, entropy: float) -> None:
        """Store result in L1 and L2 caches."""
        key = self._compute_hash(text)
        embedding = await self._embedding_provider.encode(text)

        entry = CacheEntry(
            key=key,
            text=text,
            entropy=entropy,
            embedding=embedding,
            ttl_seconds=self._ttl_seconds,
        )

        # L1: Store with hash key
        self._l1_cache[key] = entry
        self._evict_l1_if_needed()

        # L2: Store for semantic lookup
        self._l2_cache[key] = entry
        self._evict_l2_if_needed()

    def _evict_l1_if_needed(self) -> None:
        """Evict least recently used entries from L1."""
        if len(self._l1_cache) <= self._l1_max_size:
            return

        # Sort by last_accessed and remove oldest
        sorted_entries = sorted(
            self._l1_cache.items(),
            key=lambda x: x[1].last_accessed
        )

        entries_to_remove = len(self._l1_cache) - self._l1_max_size
        for key, _ in sorted_entries[:entries_to_remove]:
            del self._l1_cache[key]

    def _evict_l2_if_needed(self) -> None:
        """Evict least recently used entries from L2."""
        if len(self._l2_cache) <= self._l2_max_size:
            return

        sorted_entries = sorted(
            self._l2_cache.items(),
            key=lambda x: x[1].last_accessed
        )

        entries_to_remove = len(self._l2_cache) - self._l2_max_size
        for key, _ in sorted_entries[:entries_to_remove]:
            del self._l2_cache[key]

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._stats["total_requests"]
        if total == 0:
            hit_rate = 0.0
        else:
            hits = self._stats["l1_hits"] + self._stats["l2_hits"]
            hit_rate = hits / total

        return {
            **self._stats,
            "l1_size": len(self._l1_cache),
            "l2_size": len(self._l2_cache),
            "hit_rate": hit_rate,
        }

    def clear(self) -> None:
        """Clear all caches and reset statistics."""
        self._l1_cache.clear()
        self._l2_cache.clear()
        for key in self._stats:
            self._stats[key] = 0

    async def health_check(self) -> Dict[str, Any]:
        """Check cache health."""
        return {
            "healthy": True,
            "stats": self.get_stats(),
            "embedding_provider": type(self._embedding_provider).__name__,
        }
