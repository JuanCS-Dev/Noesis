"""
MAXIMUS 2.0 - RAG-Based Hallucination Verification
===================================================

Verifies claims against a knowledge base using RAG pattern.

Based on:
- HaluCheck: Explainable verification (2025)
- Chain-of-Verification research
- RAG-Reasoning Systems survey

Architecture:
    ┌─────────────────────────────────────────────────────────┐
    │              RAG VERIFICATION PIPELINE                   │
    ├─────────────────────────────────────────────────────────┤
    │  1. Extract claims from text                            │
    │  2. Query knowledge base for relevant context           │
    │  3. Compare claims against retrieved evidence           │
    │  4. Score verification confidence                       │
    │                                                          │
    │  Verified → Claim matches knowledge base                │
    │  Contradiction → Claim conflicts with evidence          │
    │  Unsupported → No evidence found                        │
    └─────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import asyncio
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class VerificationStatus(str, Enum):
    """Status of claim verification."""
    VERIFIED = "verified"           # Claim matches evidence
    CONTRADICTION = "contradiction"  # Claim conflicts with evidence
    UNSUPPORTED = "unsupported"      # No evidence found
    PARTIAL = "partial"              # Partial match
    ERROR = "error"                  # Verification failed


@dataclass
class RetrievedDocument:
    """Document retrieved from knowledge base."""
    content: str
    source: str
    relevance_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClaimVerification:
    """Result of verifying a single claim."""
    claim: str
    status: VerificationStatus
    confidence: float  # 0.0 to 1.0
    evidence: List[RetrievedDocument] = field(default_factory=list)
    reasoning: str = ""
    contradiction_details: Optional[str] = None


@dataclass
class VerificationResult:
    """Complete verification result for text."""
    text: str
    verified: bool
    overall_confidence: float
    claim_results: List[ClaimVerification] = field(default_factory=list)
    verified_count: int = 0
    contradiction_count: int = 0
    unsupported_count: int = 0


class KnowledgeBaseClient(ABC):  # pylint: disable=too-few-public-methods
    """Abstract client for knowledge base queries."""

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedDocument]:
        """Search knowledge base for relevant documents."""


class MockKnowledgeBaseClient(KnowledgeBaseClient):  # pylint: disable=too-few-public-methods
    """Mock knowledge base for testing."""

    def __init__(
        self,
        documents: Optional[List[RetrievedDocument]] = None
    ):
        self._documents = documents or [
            RetrievedDocument(
                content="Paris is the capital of France.",
                source="geography_facts",
                relevance_score=0.95,
            ),
            RetrievedDocument(
                content="The Eiffel Tower is located in Paris.",
                source="landmarks",
                relevance_score=0.8,
            ),
        ]

    async def search(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedDocument]:
        """Return mock documents."""
        return self._documents[:limit]


class RAGVerifier:
    """
    Verifies claims against knowledge base using RAG.

    Pipeline:
    1. Extract verifiable claims from text
    2. For each claim, query knowledge base
    3. Compare claim against retrieved evidence
    4. Score confidence based on match quality

    Usage:
        verifier = RAGVerifier(knowledge_base=qdrant_client)
        result = await verifier.verify(
            "The capital of France is Paris and it was founded in 100 BC."
        )
        print(f"Verified: {result.verified}, Confidence: {result.overall_confidence}")
    """

    # Claim extraction patterns
    CLAIM_PATTERNS = [
        r"(?:^|[.!?])\s*([A-Z][^.!?]*(?:is|are|was|were|has|have|had)[^.!?]+)[.!?]",
        r"([^.!?]+(?:contains?|includes?|consists?)[^.!?]+)[.!?]",
        r"([^.!?]+(?:located|found|situated)[^.!?]+)[.!?]",
    ]

    def __init__(
        self,
        knowledge_base: Optional[KnowledgeBaseClient] = None,
        min_relevance: float = 0.7,
        contradiction_threshold: float = 0.3,
        verification_threshold: float = 0.8,
    ):
        """
        Initialize verifier.

        Args:
            knowledge_base: Client for knowledge base queries
            min_relevance: Minimum relevance score for evidence
            contradiction_threshold: Below this similarity = contradiction
            verification_threshold: Above this similarity = verified
        """
        self._kb = knowledge_base or MockKnowledgeBaseClient()
        self._min_relevance = min_relevance
        self._contradiction_threshold = contradiction_threshold
        self._verification_threshold = verification_threshold

    async def verify(
        self,
        text: str,
        max_claims: int = 10,
    ) -> VerificationResult:
        """
        Verify all claims in text.

        Args:
            text: Text containing claims to verify
            max_claims: Maximum claims to verify

        Returns:
            VerificationResult with all claim verifications
        """
        # Extract claims
        claims = self._extract_claims(text)[:max_claims]

        if not claims:
            return VerificationResult(
                text=text,
                verified=True,
                overall_confidence=0.5,
                claim_results=[],
            )

        # Verify each claim
        verifications = await asyncio.gather(*[
            self._verify_claim(claim) for claim in claims
        ])

        # Aggregate results
        verified_count = sum(
            1 for v in verifications
            if v.status == VerificationStatus.VERIFIED
        )
        contradiction_count = sum(
            1 for v in verifications
            if v.status == VerificationStatus.CONTRADICTION
        )
        unsupported_count = sum(
            1 for v in verifications
            if v.status == VerificationStatus.UNSUPPORTED
        )

        # Overall verdict
        verified = contradiction_count == 0 and verified_count > 0
        confidence = self._calculate_confidence(verifications)

        return VerificationResult(
            text=text,
            verified=verified,
            overall_confidence=confidence,
            claim_results=verifications,
            verified_count=verified_count,
            contradiction_count=contradiction_count,
            unsupported_count=unsupported_count,
        )

    def _extract_claims(self, text: str) -> List[str]:
        """Extract verifiable claims from text."""
        claims = []

        # Simple sentence-based extraction
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:
                # Filter to likely factual claims
                claim_indicators = [
                    "is", "are", "was", "were", "has", "have",
                    "contains", "includes", "located", "founded",
                    "created", "built", "established",
                ]
                if any(ind in sentence.lower() for ind in claim_indicators):
                    claims.append(sentence)

        return claims

    async def _verify_claim(self, claim: str) -> ClaimVerification:
        """Verify a single claim against knowledge base."""
        try:
            # Query knowledge base
            docs = await self._kb.search(
                query=claim,
                limit=5,
            )

            # Filter by relevance
            relevant_docs = [
                d for d in docs
                if d.relevance_score >= self._min_relevance
            ]

            if not relevant_docs:
                return ClaimVerification(
                    claim=claim,
                    status=VerificationStatus.UNSUPPORTED,
                    confidence=0.3,
                    evidence=[],
                    reasoning="No relevant evidence found in knowledge base.",
                )

            # Compare claim to evidence
            verification = self._compare_to_evidence(claim, relevant_docs)
            return verification

        except (ValueError, KeyError, TypeError, AttributeError) as e:
            return ClaimVerification(
                claim=claim,
                status=VerificationStatus.ERROR,
                confidence=0.0,
                evidence=[],
                reasoning=f"Verification error: {str(e)}",
            )

    def _compare_to_evidence(  # pylint: disable=too-many-locals
        self,
        claim: str,
        docs: List[RetrievedDocument],
    ) -> ClaimVerification:
        """Compare claim to retrieved evidence."""
        claim_lower = claim.lower()
        claim_keywords = set(
            w for w in re.findall(r'\w+', claim_lower)
            if len(w) > 3
        )

        best_match_score = 0.0
        contradiction_found = False
        contradiction_details = None

        for doc in docs:
            doc_lower = doc.content.lower()
            doc_keywords = set(
                w for w in re.findall(r'\w+', doc_lower)
                if len(w) > 3
            )

            # Simple keyword overlap
            if claim_keywords and doc_keywords:
                overlap = len(claim_keywords & doc_keywords)
                score = overlap / len(claim_keywords)
                best_match_score = max(best_match_score, score)

            # Check for contradiction indicators
            negation_words = ["not", "never", "false", "incorrect", "wrong"]
            for neg in negation_words:
                if neg in doc_lower and neg not in claim_lower:
                    # Possible contradiction
                    shared = claim_keywords & doc_keywords
                    if len(shared) > 2:  # Significant overlap but negation
                        contradiction_found = True
                        contradiction_details = f"Evidence contradicts: {doc.content[:100]}"

        # Determine status
        if contradiction_found:
            return ClaimVerification(
                claim=claim,
                status=VerificationStatus.CONTRADICTION,
                confidence=0.8,
                evidence=docs,
                reasoning="Claim contradicts evidence in knowledge base.",
                contradiction_details=contradiction_details,
            )
        if best_match_score >= self._verification_threshold:
            return ClaimVerification(
                claim=claim,
                status=VerificationStatus.VERIFIED,
                confidence=best_match_score,
                evidence=docs,
                reasoning="Claim verified against knowledge base evidence.",
            )
        if best_match_score >= 0.4:
            return ClaimVerification(
                claim=claim,
                status=VerificationStatus.PARTIAL,
                confidence=best_match_score,
                evidence=docs,
                reasoning="Claim partially supported by evidence.",
            )
        return ClaimVerification(
            claim=claim,
            status=VerificationStatus.UNSUPPORTED,
            confidence=0.3,
            evidence=docs,
            reasoning="Insufficient evidence to verify claim.",
        )

    def _calculate_confidence(
        self,
        verifications: List[ClaimVerification],
    ) -> float:
        """Calculate overall confidence from verifications."""
        if not verifications:
            return 0.5

        # Weighted average by status
        total_weight = 0.0
        total_score = 0.0

        for v in verifications:
            weight = 1.0
            if v.status == VerificationStatus.VERIFIED:
                score = v.confidence
            elif v.status == VerificationStatus.CONTRADICTION:
                score = 0.0
                weight = 2.0  # Contradictions count more
            elif v.status == VerificationStatus.PARTIAL:
                score = v.confidence * 0.7
            else:
                score = 0.5

            total_weight += weight
            total_score += score * weight

        return total_score / total_weight if total_weight > 0 else 0.5

    async def health_check(self) -> Dict[str, Any]:
        """Check verifier health."""
        return {
            "healthy": True,
            "knowledge_base": type(self._kb).__name__,
            "min_relevance": self._min_relevance,
            "verification_threshold": self._verification_threshold,
        }
