"""
MAXIMUS 2.0 - Detection Systems
===============================

Specialized detectors for the philosophical judges:
- SemanticEntropyDetector: Measures uncertainty in claims
- TieredSemanticCache: L1/L2/L3 cache for entropy computation
- RAGVerifier: Validates claims against knowledge base
- ContextDepthAnalyzer: Measures reasoning sophistication
"""

from __future__ import annotations


from .semantic_cache import (
    CacheEntry,
    CacheLevel,
    CacheMode,
    CacheResult,
    EmbeddingProvider,
    LocalEmbeddingProvider,
    MockEmbeddingProvider,
    TieredSemanticCache,
)
from .semantic_entropy import (
    EntropyResult,
    LLMProvider,
    MockLLMProvider,
    SemanticEntropyDetector,
)
from .hallucination import (
    ClaimVerification,
    KnowledgeBaseClient,
    MockKnowledgeBaseClient,
    RAGVerifier,
    RetrievedDocument,
    VerificationResult,
    VerificationStatus,
)
from .context_depth import (
    ContextDepthAnalyzer,
    DepthAnalysis,
)

__all__ = [
    # Semantic Cache
    "CacheEntry",
    "CacheLevel",
    "CacheMode",
    "CacheResult",
    "EmbeddingProvider",
    "LocalEmbeddingProvider",
    "MockEmbeddingProvider",
    "TieredSemanticCache",
    # Semantic Entropy
    "EntropyResult",
    "LLMProvider",
    "MockLLMProvider",
    "SemanticEntropyDetector",
    # Hallucination/RAG
    "ClaimVerification",
    "KnowledgeBaseClient",
    "MockKnowledgeBaseClient",
    "RAGVerifier",
    "RetrievedDocument",
    "VerificationResult",
    "VerificationStatus",
    # Context Depth
    "ContextDepthAnalyzer",
    "DepthAnalysis",
]
