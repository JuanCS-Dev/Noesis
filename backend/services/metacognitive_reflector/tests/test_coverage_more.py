"""
Additional tests to improve coverage.
"""

from __future__ import annotations


import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from metacognitive_reflector.core.judges.base import JudgePlugin, JudgeVerdict, VerdictType
from metacognitive_reflector.core.judges.arbiter import EnsembleArbiter
from metacognitive_reflector.core.judges.resilience import ResilientJudgeWrapper
from metacognitive_reflector.core.judges.voting import (
    TribunalDecision,
    VoteResult,
    calculate_consensus,
    calculate_votes,
    determine_decision,
)
from metacognitive_reflector.core.detectors.context_depth import (
    ContextDepthAnalyzer,
    DepthAnalysis,
)
from metacognitive_reflector.core.detectors.semantic_entropy import SemanticEntropyDetector
from metacognitive_reflector.core.detectors.hallucination import RAGVerifier


class MockJudge(JudgePlugin):
    """Mock judge for testing."""

    def __init__(
        self,
        name: str = "MOCK",
        pillar: str = "Test",
        result_passed: bool = True,
        confidence: float = 0.9,
    ):
        self._name = name
        self._pillar = pillar
        self._result_passed = result_passed
        self._confidence = confidence

    @property
    def name(self) -> str:
        return self._name

    @property
    def pillar(self) -> str:
        return self._pillar

    @property
    def weight(self) -> float:
        return 0.33

    async def evaluate(self, execution_log, context=None):
        return JudgeVerdict(
            judge_name=self.name,
            pillar=self.pillar,
            verdict=VerdictType.PASS if self._result_passed else VerdictType.FAIL,
            passed=self._result_passed,
            confidence=self._confidence,
            reasoning="Mock evaluation",
        )

    async def get_evidence(self, execution_log, context=None):
        return []


class TestVotingEdgeCases:
    """Tests for voting edge cases."""

    def test_calculate_consensus_all_abstained(self):
        """Test consensus when all abstained."""
        votes = [
            VoteResult(
                judge_name="A",
                pillar="P",
                vote=None,
                weight=0.5,
                confidence=0.0,
                weighted_vote=0.0,
                abstained=True,
            ),
            VoteResult(
                judge_name="B",
                pillar="P",
                vote=None,
                weight=0.5,
                confidence=0.0,
                weighted_vote=0.0,
                abstained=True,
            ),
        ]

        consensus = calculate_consensus(votes)
        # When all abstained, consensus should return a default value
        assert 0 <= consensus <= 1

    def test_determine_decision_edge_cases(self):
        """Test decision at exact thresholds."""
        # Exactly at pass threshold
        assert determine_decision(0.70, 0.70, 0.50) == TribunalDecision.PASS

        # Just below pass, above review
        assert determine_decision(0.69, 0.70, 0.50) == TribunalDecision.REVIEW

        # Exactly at review threshold
        assert determine_decision(0.50, 0.70, 0.50) == TribunalDecision.REVIEW

        # Just below review
        assert determine_decision(0.49, 0.70, 0.50) == TribunalDecision.FAIL


class TestEnsembleArbiterEdgeCases:
    """Tests for EnsembleArbiter edge cases."""

    @pytest.mark.asyncio
    async def test_deliberate_mixed_verdicts(self):
        """Test deliberation with mixed pass/fail."""
        judges = [
            MockJudge("VERITAS", "Truth", result_passed=True, confidence=0.9),
            MockJudge("SOPHIA", "Wisdom", result_passed=False, confidence=0.8),
            MockJudge("DIKĒ", "Justice", result_passed=True, confidence=0.85),
        ]

        arbiter = EnsembleArbiter(judges, use_resilience=False)
        verdict = await arbiter.deliberate({"task": "test"})

        # Should still pass with 2 out of 3 passing
        assert verdict.decision in [TribunalDecision.PASS, TribunalDecision.REVIEW]

    @pytest.mark.asyncio
    async def test_deliberate_all_fail(self):
        """Test deliberation with all failing."""
        judges = [
            MockJudge("VERITAS", "Truth", result_passed=False, confidence=0.9),
            MockJudge("SOPHIA", "Wisdom", result_passed=False, confidence=0.8),
            MockJudge("DIKĒ", "Justice", result_passed=False, confidence=0.85),
        ]

        arbiter = EnsembleArbiter(judges, use_resilience=False)
        verdict = await arbiter.deliberate({"task": "test"})

        assert verdict.decision == TribunalDecision.FAIL


class TestResilientJudgeWrapperEdgeCases:
    """Tests for ResilientJudgeWrapper edge cases."""

    @pytest.mark.asyncio
    async def test_wrapper_properties(self):
        """Test wrapper exposes judge properties."""
        judge = MockJudge("TEST", "Test Pillar")
        wrapper = ResilientJudgeWrapper(judge)

        assert wrapper.name == "TEST"
        assert wrapper.pillar == "Test Pillar"

    @pytest.mark.asyncio
    async def test_wrapper_successful_evaluation(self):
        """Test successful evaluation through wrapper."""
        judge = MockJudge("TEST", "Test")
        wrapper = ResilientJudgeWrapper(judge)

        verdict = await wrapper.evaluate({"task": "test"})

        assert verdict.passed is True
        assert verdict.judge_name == "TEST"


class TestContextDepthAnalyzerEdgeCases:
    """Tests for ContextDepthAnalyzer edge cases."""

    @pytest.mark.asyncio
    async def test_analyze_empty_input(self):
        """Test analyzing empty input."""
        analyzer = ContextDepthAnalyzer()

        result = await analyzer.analyze(
            action=None,
            outcome=None,
            reasoning_trace=None,
        )

        assert isinstance(result, DepthAnalysis)
        # Empty input returns default scores
        assert 0 <= result.depth_score <= 1

    @pytest.mark.asyncio
    async def test_analyze_very_short_input(self):
        """Test analyzing very short input."""
        analyzer = ContextDepthAnalyzer()

        result = await analyzer.analyze(
            action="OK",
            outcome="Yes",
            reasoning_trace="",
        )

        assert isinstance(result, DepthAnalysis)

    @pytest.mark.asyncio
    async def test_analyze_with_reasoning_trace(self):
        """Test analyzing with full reasoning trace."""
        analyzer = ContextDepthAnalyzer()

        result = await analyzer.analyze(
            action="Analyzed the data",
            outcome="Found patterns",
            reasoning_trace="First I examined the input. Then I processed it. Finally I concluded.",
        )

        assert isinstance(result, DepthAnalysis)
        assert result.cot_score > 0  # Should detect chain of thought

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check."""
        analyzer = ContextDepthAnalyzer()
        health = await analyzer.health_check()

        assert health["healthy"] is True


class TestSemanticEntropyDetectorEdgeCases:
    """Tests for SemanticEntropyDetector edge cases."""

    @pytest.mark.asyncio
    async def test_compute_entropy_empty(self):
        """Test entropy for empty text."""
        detector = SemanticEntropyDetector()
        entropy = await detector.compute_entropy("")
        assert isinstance(entropy, float)

    @pytest.mark.asyncio
    async def test_compute_entropy_certain(self):
        """Test entropy for certain statement."""
        detector = SemanticEntropyDetector()
        entropy = await detector.compute_entropy(
            "2 + 2 = 4. This is a mathematical fact."
        )
        assert isinstance(entropy, float)
        # Factual statements should have lower entropy
        assert entropy < 0.8


class TestRAGVerifierEdgeCases:
    """Tests for RAGVerifier edge cases."""

    @pytest.mark.asyncio
    async def test_verify_empty_text(self):
        """Test verification of empty text."""
        verifier = RAGVerifier()
        result = await verifier.verify("")
        assert result.verified is True  # Empty = no claims to fail

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check."""
        verifier = RAGVerifier()
        health = await verifier.health_check()
        assert health["healthy"] is True
