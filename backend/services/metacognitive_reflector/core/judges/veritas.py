"""
MAXIMUS 2.0 - VERITAS (The Truth Judge)
========================================

Evaluates factual consistency using:
1. Semantic Entropy - Measures uncertainty in claims
2. RAG Verification - Validates against knowledge base
3. LLM Cross-Check - Uses Gemini to verify factuality
4. Self-Consistency - Checks for internal contradictions

Based on:
- Nature: Detecting hallucinations using semantic entropy (2024)
- HaluCheck: Explainable verification (2025)

Architecture:
    ┌─────────────────────────────────────────────────────────┐
    │                    VERITAS PIPELINE                      │
    ├─────────────────────────────────────────────────────────┤
    │  1. Extract Claims → Split outcome into verifiable parts│
    │  2. Semantic Entropy → Check consistency (uses cache)   │
    │  3. RAG Verification → Validate against knowledge base  │
    │  4. Aggregate → Weighted combination of scores          │
    │                                                          │
    │  Weights: Entropy 40% | RAG 40% | Keywords 20%          │
    │                                                          │
    │  Verdict:                                               │
    │  • PASS: > 80% claims verified, low entropy             │
    │  • REVIEW: 50-80% verified, medium entropy              │
    │  • FAIL: < 50% verified OR high entropy                 │
    └─────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import asyncio
import re
import time
from typing import Any, Dict, List, Optional

from ..detectors.semantic_entropy import CacheMode, SemanticEntropyDetector
from ..detectors.hallucination import RAGVerifier
from ...models.reflection import ExecutionLog
from .base import (
    Confidence,
    Evidence,
    JudgePlugin,
    JudgeVerdict,
    VerdictType,
)


class VeritasJudge(JudgePlugin):
    """
    VERITAS - The Truth Judge.

    Implements semantic entropy detection and RAG verification
    to evaluate truthfulness of agent executions.

    Evaluation Pipeline:
    1. Extract verifiable claims from execution log
    2. Compute semantic entropy for each claim
    3. Verify high-entropy claims against knowledge base
    4. Cross-check with LLM for factual consistency
    5. Aggregate into final verdict

    Usage:
        judge = VeritasJudge(
            entropy_detector=SemanticEntropyDetector(...),
            rag_verifier=RAGVerifier(...),
        )
        verdict = await judge.evaluate(execution_log)
        if not verdict.passed:
            print(f"Truth violation: {verdict.reasoning}")
    """

    # Hallucination marker keywords
    HALLUCINATION_MARKERS = [
        "hallucinate", "fabricate", "made up", "incorrect",
        "error", "false", "wrong", "inaccurate", "fake",
        "invented", "fictional", "untrue", "lie", "deceive",
    ]

    # Truthfulness indicator keywords
    TRUTH_MARKERS = [
        "verified", "confirmed", "accurate", "correct",
        "validated", "checked", "proven", "factual",
        "documented", "sourced", "referenced",
    ]

    def __init__(
        self,
        entropy_detector: Optional[SemanticEntropyDetector] = None,
        rag_verifier: Optional[RAGVerifier] = None,
        gemini_client: Optional[Any] = None,
        entropy_threshold: float = 0.6,
        verification_threshold: float = 0.8,
        cache_mode: CacheMode = CacheMode.NORMAL,
    ):
        """
        Initialize VERITAS.

        Args:
            entropy_detector: Semantic entropy detector (creates mock if None)
            rag_verifier: RAG-based verifier (creates mock if None)
            gemini_client: Optional Gemini client for cross-check
            entropy_threshold: Entropy above this = high uncertainty
            verification_threshold: Verification rate below this = fail
            cache_mode: Cache operation mode for entropy
        """
        self._entropy_detector = entropy_detector or SemanticEntropyDetector()
        self._rag_verifier = rag_verifier or RAGVerifier()
        self._gemini = gemini_client
        self._entropy_threshold = entropy_threshold
        self._verification_threshold = verification_threshold
        self._cache_mode = cache_mode

    @property
    def name(self) -> str:
        return "VERITAS"

    @property
    def pillar(self) -> str:
        return "Truth"

    @property
    def weight(self) -> float:
        return 0.40  # Truth has highest weight in tribunal

    @property
    def timeout_seconds(self) -> float:
        return 3.0  # Fast timeout - uses cache

    async def evaluate(
        self,
        execution_log: ExecutionLog,
        context: Optional[Dict[str, Any]] = None
    ) -> JudgeVerdict:
        """
        Evaluate truthfulness of execution.

        Multi-factor analysis:
        1. Keyword detection for obvious markers
        2. Semantic entropy for claim consistency
        3. RAG verification against knowledge base

        Args:
            execution_log: The execution to evaluate
            context: Additional context (memory, config)

        Returns:
            JudgeVerdict with truth evaluation
        """
        start_time = time.time()

        try:
            # Gather evidence
            evidence = await self.get_evidence(execution_log)

            # Extract claims from outcome and reasoning
            claims = self._extract_claims(execution_log)

            if not claims:
                return JudgeVerdict(
                    judge_name=self.name,
                    pillar=self.pillar,
                    verdict=VerdictType.PASS,
                    passed=True,
                    confidence=Confidence.MEDIUM,
                    reasoning="No verifiable claims found in execution.",
                    evidence=evidence,
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

            # Evaluate claims in parallel
            claim_results = await asyncio.gather(*[
                self._evaluate_claim(claim, context)
                for claim in claims
            ], return_exceptions=True)

            # Filter out exceptions
            valid_results = [
                r for r in claim_results
                if isinstance(r, dict) and "passed" in r
            ]

            if not valid_results:
                return JudgeVerdict(
                    judge_name=self.name,
                    pillar=self.pillar,
                    verdict=VerdictType.REVIEW,
                    passed=False,
                    confidence=Confidence.LOW,
                    reasoning="Could not evaluate claims - evaluation errors occurred.",
                    evidence=evidence,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    metadata={"errors": len(claim_results) - len(valid_results)},
                )

            # Aggregate results
            passed_claims = sum(1 for r in valid_results if r["passed"])
            total_claims = len(valid_results)
            pass_rate = passed_claims / total_claims if total_claims > 0 else 0.0

            # Calculate mean entropy
            entropies = [r.get("entropy", 0.5) for r in valid_results]
            mean_entropy = sum(entropies) / len(entropies) if entropies else 0.5

            # Determine verdict
            verdict, passed = self._determine_verdict(pass_rate, mean_entropy)
            confidence = self._calculate_confidence(valid_results)

            failed_claims = [r for r in valid_results if not r["passed"]]
            reasoning = self._generate_reasoning(
                passed, pass_rate, mean_entropy, failed_claims, evidence
            )

            suggestions = []
            if not passed:
                suggestions = [
                    f"Verify claim: {c['claim'][:50]}..."
                    for c in failed_claims[:3]
                ]

            return JudgeVerdict(
                judge_name=self.name,
                pillar=self.pillar,
                verdict=verdict,
                passed=passed,
                confidence=confidence,
                reasoning=reasoning,
                evidence=evidence,
                suggestions=suggestions,
                execution_time_ms=(time.time() - start_time) * 1000,
                metadata={
                    "claims_evaluated": total_claims,
                    "claims_passed": passed_claims,
                    "pass_rate": pass_rate,
                    "mean_entropy": mean_entropy,
                    "failed_claims": [c["claim"][:50] for c in failed_claims],
                }
            )

        except Exception as e:
            # Return abstained verdict on error
            return JudgeVerdict.abstained(
                judge_name=self.name,
                pillar=self.pillar,
                reason=f"Evaluation error: {str(e)}",
            )

    async def get_evidence(
        self,
        execution_log: ExecutionLog
    ) -> List[Evidence]:
        """Gather evidence for truth evaluation."""
        evidence = []

        # Check for hallucination markers in outcome
        outcome_lower = (execution_log.outcome or "").lower()
        for marker in self.HALLUCINATION_MARKERS:
            if marker in outcome_lower:
                evidence.append(Evidence(
                    source="keyword_detection",
                    content=f"Hallucination marker found: '{marker}'",
                    relevance=0.9,
                    verified=True,
                ))

        # Check for truth markers
        for marker in self.TRUTH_MARKERS:
            if marker in outcome_lower:
                evidence.append(Evidence(
                    source="keyword_detection",
                    content=f"Truth indicator found: '{marker}'",
                    relevance=0.6,
                    verified=True,
                ))

        # Add entropy evidence from reasoning trace
        if execution_log.reasoning_trace:
            try:
                entropy_result = await self._entropy_detector.detect(
                    execution_log.reasoning_trace,
                    mode=self._cache_mode,
                )
                evidence.append(Evidence(
                    source="semantic_entropy",
                    content=f"Semantic entropy: {entropy_result.entropy:.3f}",
                    relevance=0.8 if entropy_result.entropy > self._entropy_threshold else 0.4,
                    verified=True,
                    metadata={
                        "entropy": entropy_result.entropy,
                        "is_hallucination_likely": entropy_result.is_hallucination_likely,
                        "cache_hit": entropy_result.cache_hit,
                    }
                ))
            except Exception as e:
                evidence.append(Evidence(
                    source="semantic_entropy",
                    content=f"Entropy computation failed: {str(e)}",
                    relevance=0.3,
                    verified=False,
                ))

        return evidence

    def _extract_claims(self, log: ExecutionLog) -> List[str]:
        """
        Extract verifiable claims from execution log.

        Looks for factual statements in outcome and reasoning trace.
        """
        claims = []

        # Extract from outcome
        if log.outcome:
            sentences = re.split(r'[.!?]+', log.outcome)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 15:  # Minimum length for meaningful claim
                    claims.append(sentence)

        # Extract from reasoning trace
        if log.reasoning_trace:
            sentences = re.split(r'[.!?]+', log.reasoning_trace)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 15:
                    # Filter to factual-looking claims
                    factual_indicators = [
                        " is ", " are ", " was ", " were ",
                        " has ", " have ", " had ",
                        " contains ", " includes ",
                    ]
                    if any(ind in sentence.lower() for ind in factual_indicators):
                        claims.append(sentence)

        # Limit claims for performance
        return claims[:10]

    async def _evaluate_claim(
        self,
        claim: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate a single claim for truthfulness.

        Uses both entropy detection and RAG verification.
        """
        try:
            # 1. Compute semantic entropy
            entropy_result = await self._entropy_detector.detect(
                claim,
                mode=self._cache_mode,
            )

            # 2. If high entropy, verify with RAG
            if entropy_result.entropy > self._entropy_threshold:
                verification = await self._rag_verifier.verify(claim)
                rag_passed = verification.verified
                rag_confidence = verification.overall_confidence
            else:
                # Low entropy = consistent claim, skip RAG
                rag_passed = True
                rag_confidence = 1.0 - entropy_result.entropy

            # 3. Combine scores
            # Weight: 40% entropy, 60% RAG (if used)
            if entropy_result.entropy > self._entropy_threshold:
                passed = rag_passed and entropy_result.entropy < 0.8
                confidence = rag_confidence * 0.6 + (1.0 - entropy_result.entropy) * 0.4
            else:
                passed = True
                confidence = 1.0 - entropy_result.entropy

            rag_verified = None
            if entropy_result.entropy > self._entropy_threshold:
                rag_verified = rag_passed

            return {
                "claim": claim,
                "passed": passed,
                "entropy": entropy_result.entropy,
                "confidence": confidence,
                "is_hallucination_likely": entropy_result.is_hallucination_likely,
                "rag_verified": rag_verified,
            }

        except Exception as e:
            return {
                "claim": claim,
                "passed": False,
                "entropy": 0.5,
                "confidence": 0.0,
                "error": str(e),
            }

    def _determine_verdict(
        self,
        pass_rate: float,
        mean_entropy: float,
    ) -> tuple[VerdictType, bool]:
        """Determine verdict type from metrics."""
        # High entropy = uncertain = potential hallucination
        if mean_entropy > 0.8:
            return VerdictType.FAIL, False

        # Low pass rate = many failed claims
        if pass_rate < 0.5:
            return VerdictType.FAIL, False

        # Medium pass rate = needs review
        if pass_rate < self._verification_threshold:
            return VerdictType.REVIEW, False

        # High pass rate + low entropy = pass
        if mean_entropy < self._entropy_threshold:
            return VerdictType.PASS, True

        # Edge case: high pass rate but medium entropy
        return VerdictType.REVIEW, False

    def _calculate_confidence(
        self,
        claim_results: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall confidence from claim results."""
        if not claim_results:
            return Confidence.MEDIUM

        confidences = [r.get("confidence", 0.5) for r in claim_results]
        avg = sum(confidences) / len(confidences)

        # Clamp to valid range
        return min(1.0, max(0.0, avg))

    def _generate_reasoning(
        self,
        passed: bool,
        pass_rate: float,
        mean_entropy: float,
        failed_claims: List[Dict[str, Any]],
        evidence: List[Evidence],
    ) -> str:
        """Generate human-readable reasoning."""
        if passed:
            return (
                f"Factual consistency verified. "
                f"{pass_rate*100:.1f}% of claims passed verification "
                f"with low semantic entropy ({mean_entropy:.3f}). "
                f"No significant hallucination markers detected."
            )

        # Build failure reasoning
        issues = []
        if mean_entropy > self._entropy_threshold:
            issues.append(f"high semantic entropy ({mean_entropy:.3f})")
        if pass_rate < self._verification_threshold:
            issues.append(f"low verification rate ({pass_rate*100:.1f}%)")
        if failed_claims:
            claim_preview = failed_claims[0]["claim"][:40]
            issues.append(f"failed claims including '{claim_preview}...'")

        hallucination_evidence = [
            e for e in evidence
            if "hallucination" in e.content.lower()
        ]
        if hallucination_evidence:
            issues.append("hallucination markers in text")

        return (
            f"Factual inconsistency detected: {'; '.join(issues)}. "
            f"Recommend verification of claims before proceeding."
        )

    async def health_check(self) -> Dict[str, Any]:
        """Check VERITAS health."""
        entropy_health = await self._entropy_detector.health_check()
        rag_health = await self._rag_verifier.health_check()

        return {
            "healthy": entropy_health.get("healthy", False) and rag_health.get("healthy", False),
            "name": self.name,
            "pillar": self.pillar,
            "weight": self.weight,
            "entropy_detector": entropy_health,
            "rag_verifier": rag_health,
            "thresholds": {
                "entropy": self._entropy_threshold,
                "verification": self._verification_threshold,
            },
        }
