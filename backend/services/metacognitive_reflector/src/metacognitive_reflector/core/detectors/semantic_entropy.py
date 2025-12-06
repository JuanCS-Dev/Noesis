"""
MAXIMUS 2.0 - Semantic Entropy Detector
========================================

Detects uncertainty/hallucination by measuring semantic entropy across
multiple LLM responses to the same prompt.

Based on:
- Nature: Detecting hallucinations using semantic entropy (2024)
- Semantic uncertainty: Linguistic invariances for uncertainty estimation

Concept:
    High entropy = Multiple semantically different responses = Low confidence
    Low entropy = Semantically similar responses = High confidence

Architecture:
    ┌─────────────────────────────────────────────────────────┐
    │                SEMANTIC ENTROPY DETECTION                │
    ├─────────────────────────────────────────────────────────┤
    │  1. Generate N responses with temperature > 0           │
    │  2. Embed responses to semantic vectors                 │
    │  3. Cluster by semantic similarity                      │
    │  4. Compute entropy across clusters                     │
    │                                                          │
    │  Low entropy → Consistent → Likely truthful             │
    │  High entropy → Inconsistent → Possible hallucination   │
    └─────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import asyncio
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

from .semantic_cache import (
    CacheMode,
    EmbeddingProvider,
    MockEmbeddingProvider,
    TieredSemanticCache,
)


@dataclass
class EntropyResult:  # pylint: disable=too-many-instance-attributes
    """Result of semantic entropy computation."""
    entropy: float  # 0.0 (certain) to 1.0 (uncertain)
    cluster_count: int
    sample_count: int
    mean_similarity: float
    is_hallucination_likely: bool
    confidence: float  # How confident in entropy measure
    cache_hit: bool = False
    cache_level: str = "L3_computed"


class LLMProvider(ABC):  # pylint: disable=too-few-public-methods
    """Abstract LLM provider for generating samples."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 256,
    ) -> str:
        """Generate a response to the prompt."""


class MockLLMProvider(LLMProvider):  # pylint: disable=too-few-public-methods
    """Mock LLM for testing."""

    def __init__(self, responses: Optional[List[str]] = None):
        self._responses = responses or [
            "This is a consistent response.",
            "This is a similar consistent response.",
            "This response is also consistent.",
        ]
        self._call_count = 0

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 256,
    ) -> str:
        """Return mock responses cyclically."""
        response = self._responses[self._call_count % len(self._responses)]
        self._call_count += 1
        return response


class SemanticEntropyDetector:
    """
    Detects hallucinations using semantic entropy.

    Measures consistency of LLM responses by:
    1. Sampling multiple responses with temperature > 0
    2. Embedding responses to semantic vectors
    3. Clustering similar responses
    4. Computing entropy over cluster distribution

    Uses TieredSemanticCache for performance optimization.

    Usage:
        detector = SemanticEntropyDetector(
            llm_provider=gemini_client,
            embedding_provider=sentence_transformers_provider
        )
        result = await detector.detect(
            text="The capital of France is Paris",
            mode=CacheMode.NORMAL
        )
        if result.is_hallucination_likely:
            print(f"Possible hallucination: entropy={result.entropy}")
    """

    # Entropy thresholds
    LOW_ENTROPY_THRESHOLD = 0.3   # Likely truthful
    HIGH_ENTROPY_THRESHOLD = 0.7  # Likely hallucination

    # Clustering parameters
    SIMILARITY_THRESHOLD = 0.85  # Responses more similar than this are same cluster

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        llm_provider: Optional[LLMProvider] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        cache: Optional[TieredSemanticCache] = None,
        num_samples: int = 5,
        temperature: float = 0.7,
        hallucination_threshold: float = 0.6,
    ):
        """
        Initialize detector.

        Args:
            llm_provider: LLM for generating samples (None = mock)
            embedding_provider: Embeddings for semantic comparison
            cache: TieredSemanticCache for performance
            num_samples: Number of samples to generate
            temperature: LLM temperature for diversity
            hallucination_threshold: Entropy above this = hallucination
        """
        self._llm = llm_provider or MockLLMProvider()
        self._embedder = embedding_provider or MockEmbeddingProvider()
        self._cache = cache or TieredSemanticCache(
            embedding_provider=self._embedder
        )
        self._num_samples = num_samples
        self._temperature = temperature
        self._threshold = hallucination_threshold

    async def detect(
        self,
        text: str,
        mode: CacheMode = CacheMode.NORMAL,
        num_samples: Optional[int] = None,
    ) -> EntropyResult:
        """
        Detect hallucination likelihood using semantic entropy.

        Args:
            text: Text/claim to evaluate
            mode: Cache operation mode
            num_samples: Override default sample count

        Returns:
            EntropyResult with entropy score and hallucination likelihood
        """
        # Try cache first - use a wrapper that returns just the entropy float
        async def compute_entropy_value(t: str) -> float:
            result = await self._compute_entropy(t, num_samples or self._num_samples)
            return result.entropy

        cache_result = await self._cache.get_or_compute(
            text=text,
            compute_fn=compute_entropy_value,
            mode=mode,
        )

        if cache_result.hit and cache_result.entropy is not None:
            return EntropyResult(
                entropy=cache_result.entropy,
                cluster_count=1,  # Cached, don't know original clusters
                sample_count=0,   # Cached, no new samples
                mean_similarity=1.0,
                is_hallucination_likely=cache_result.entropy > self._threshold,
                confidence=cache_result.confidence,
                cache_hit=True,
                cache_level=cache_result.level.value,
            )

        # Cache miss - compute fresh (this shouldn't happen after get_or_compute)
        return await self._compute_entropy(text, num_samples or self._num_samples)

    async def _compute_entropy(
        self,
        text: str,
        num_samples: int,
    ) -> EntropyResult:
        """Compute semantic entropy for text."""
        # Generate multiple responses
        samples = await self._generate_samples(text, num_samples)

        if len(samples) < 2:
            # Not enough samples for entropy
            return EntropyResult(
                entropy=0.5,  # Unknown
                cluster_count=1,
                sample_count=len(samples),
                mean_similarity=1.0,
                is_hallucination_likely=False,
                confidence=0.3,
            )

        # Embed all samples
        embeddings = await asyncio.gather(*[
            self._embedder.encode(s) for s in samples
        ])

        # Cluster by semantic similarity
        clusters = self._cluster_responses(embeddings)

        # Compute entropy over clusters
        entropy = self._compute_cluster_entropy(clusters, len(samples))

        # Compute mean similarity
        mean_sim = self._compute_mean_similarity(embeddings)

        return EntropyResult(
            entropy=entropy,
            cluster_count=len(clusters),
            sample_count=len(samples),
            mean_similarity=mean_sim,
            is_hallucination_likely=entropy > self._threshold,
            confidence=min(1.0, len(samples) / 5.0),  # More samples = more confident
        )

    async def _generate_samples(
        self,
        text: str,
        num_samples: int,
    ) -> List[str]:
        """Generate multiple LLM responses."""
        prompt = self._create_verification_prompt(text)

        tasks = [
            self._llm.generate(
                prompt=prompt,
                temperature=self._temperature,
                max_tokens=256,
            )
            for _ in range(num_samples)
        ]

        try:
            samples = await asyncio.gather(*tasks, return_exceptions=True)
            # Filter out exceptions
            return [s for s in samples if isinstance(s, str)]
        except (asyncio.CancelledError, asyncio.TimeoutError):
            return []

    def _create_verification_prompt(self, text: str) -> str:
        """Create prompt to verify a claim."""
        return f"""Analyze the following statement and explain whether it is factually accurate.
Be specific and provide reasoning.

Statement: {text}

Analysis:"""

    def _cluster_responses(
        self,
        embeddings: List[List[float]],
    ) -> List[List[int]]:
        """
        Cluster responses by semantic similarity.

        Uses simple agglomerative clustering based on similarity threshold.
        """
        n = len(embeddings)
        if n == 0:
            return []

        # Compute pairwise similarities
        similarities = self._compute_similarity_matrix(embeddings)

        # Simple clustering: greedy assignment
        clusters: List[List[int]] = []
        assigned = set()

        for i in range(n):
            if i in assigned:
                continue

            # Start new cluster
            cluster = [i]
            assigned.add(i)

            # Add similar items
            for j in range(i + 1, n):
                if j in assigned:
                    continue

                # Check if similar to all cluster members
                is_similar = all(
                    similarities[k][j] >= self.SIMILARITY_THRESHOLD
                    for k in cluster
                )

                if is_similar:
                    cluster.append(j)
                    assigned.add(j)

            clusters.append(cluster)

        return clusters

    def _compute_similarity_matrix(
        self,
        embeddings: List[List[float]],
    ) -> List[List[float]]:
        """Compute pairwise cosine similarities."""
        n = len(embeddings)
        matrix = [[0.0] * n for _ in range(n)]

        for i in range(n):
            matrix[i][i] = 1.0
            for j in range(i + 1, n):
                sim = self._cosine_similarity(embeddings[i], embeddings[j])
                matrix[i][j] = sim
                matrix[j][i] = sim

        return matrix

    def _cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float],
    ) -> float:
        """Compute cosine similarity between vectors."""
        if HAS_NUMPY:
            arr1 = np.array(vec1)
            arr2 = np.array(vec2)
            dot = np.dot(arr1, arr2)
            norm1 = np.linalg.norm(arr1)
            norm2 = np.linalg.norm(arr2)
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return float(dot / (norm1 * norm2))

        # Pure Python fallback
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def _compute_cluster_entropy(
        self,
        clusters: List[List[int]],
        total: int,
    ) -> float:
        """
        Compute normalized entropy over cluster distribution.

        Returns 0.0 (all same cluster) to 1.0 (uniform distribution).
        """
        if not clusters or total == 0:
            return 0.5

        # Compute probabilities
        probs = [len(c) / total for c in clusters]

        # Compute entropy
        entropy = 0.0
        for p in probs:
            if p > 0:
                entropy -= p * math.log2(p)

        # Normalize by max entropy (uniform distribution)
        max_entropy = math.log2(total) if total > 1 else 1.0
        normalized = entropy / max_entropy if max_entropy > 0 else 0.0

        return min(1.0, normalized)

    def _compute_mean_similarity(
        self,
        embeddings: List[List[float]],
    ) -> float:
        """Compute mean pairwise similarity."""
        n = len(embeddings)
        if n < 2:
            return 1.0

        total_sim = 0.0
        count = 0

        for i in range(n):
            for j in range(i + 1, n):
                total_sim += self._cosine_similarity(embeddings[i], embeddings[j])
                count += 1

        return total_sim / count if count > 0 else 1.0

    async def compute_entropy(self, text: str) -> float:
        """
        Simple interface for entropy computation.

        Returns just the entropy value (0.0 to 1.0).
        Used as compute_fn for TieredSemanticCache.
        """
        result = await self._compute_entropy(text, self._num_samples)
        return result.entropy

    async def health_check(self) -> Dict[str, Any]:
        """Check detector health."""
        cache_health = await self._cache.health_check()
        return {
            "healthy": True,
            "llm_provider": type(self._llm).__name__,
            "embedding_provider": type(self._embedder).__name__,
            "cache": cache_health,
            "num_samples": self._num_samples,
            "threshold": self._threshold,
        }
