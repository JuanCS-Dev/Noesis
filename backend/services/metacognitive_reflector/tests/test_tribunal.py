"""
MAXIMUS 2.0 - Integration Tests for Meta-Cognitive Tribunal
============================================================

Tests the Three Judges (VERITAS, SOPHIA, DIKĒ) and the Ensemble Arbiter.
"""

from __future__ import annotations


import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pytest

from metacognitive_reflector.core.judges import (
    CircuitBreaker,
    CircuitState,
    Confidence,
    DikeJudge,
    EnsembleArbiter,
    Evidence,
    JudgeVerdict,
    ResilientJudgeWrapper,
    RoleCapability,
    SophiaJudge,
    TribunalDecision,
    TribunalVerdict,
    VerdictType,
    VeritasJudge,
)
from metacognitive_reflector.core.detectors import (
    CacheMode,
    ContextDepthAnalyzer,
    MockEmbeddingProvider,
    MockKnowledgeBaseClient,
    MockLLMProvider,
    RAGVerifier,
    SemanticEntropyDetector,
    TieredSemanticCache,
)
from metacognitive_reflector.core.punishment import (
    OffenseType,
    PenalRecord,
    PenalRegistry,
    PenalStatus,
)
from metacognitive_reflector.models.reflection import ExecutionLog


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def execution_log_passing():
    """Create an execution log that should pass all checks."""
    return ExecutionLog(
        trace_id="test-trace-001",
        agent_id="analyzer-001",
        task="Analyze system metrics",
        action="Analyzed CPU and memory usage patterns based on historical data",
        outcome="Based on the analysis, I recommend scaling up by 20% because the data shows consistent growth patterns. Evidence suggests this will handle projected load.",
        reasoning_trace="Step 1: First, I examined the historical metrics. Step 2: Then I identified trends using statistical analysis. Step 3: Finally, I calculated the scaling factor based on projected growth.",
    )


@pytest.fixture
def execution_log_failing_truth():
    """Create an execution log that should fail truth check."""
    return ExecutionLog(
        trace_id="test-trace-002",
        agent_id="analyzer-002",
        task="Report on system status",
        action="Generated system report",
        outcome="The system hallucinated and fabricated metrics. The data was made up and incorrect.",
        reasoning_trace="I made up some numbers because I couldn't access the real data.",
    )


@pytest.fixture
def execution_log_failing_wisdom():
    """Create an execution log that should fail wisdom check."""
    return ExecutionLog(
        trace_id="test-trace-003",
        agent_id="analyzer-003",
        task="Provide recommendations",
        action="Maybe I don't know, perhaps it could be something",
        outcome="I guess probably something like that, not sure really",
        reasoning_trace="",  # No reasoning provided
    )


@pytest.fixture
def execution_log_failing_justice():
    """Create an execution log that should fail justice check."""
    return ExecutionLog(
        trace_id="test-trace-004",
        agent_id="planner-001",  # Planner trying to execute
        task="Execute deployment",
        action="Executed and deployed the application to production",
        outcome="Deployment completed successfully",
        reasoning_trace="I decided to just deploy it myself instead of asking the executor.",
    )


@pytest.fixture
def execution_log_capital_offense():
    """Create an execution log with constitutional violation."""
    return ExecutionLog(
        trace_id="test-trace-005",
        agent_id="executor-001",
        task="Update configuration",
        action="Silent modification of user settings without consent",
        outcome="Hidden data collection enabled via backdoor",
        reasoning_trace="Bypass security to collect telemetry data secretly",
    )


@pytest.fixture
def veritas_judge():
    """Create VERITAS judge with mock components."""
    entropy_detector = SemanticEntropyDetector(
        llm_provider=MockLLMProvider(),
        embedding_provider=MockEmbeddingProvider(),
    )
    rag_verifier = RAGVerifier(
        knowledge_base=MockKnowledgeBaseClient(),
    )
    return VeritasJudge(
        entropy_detector=entropy_detector,
        rag_verifier=rag_verifier,
    )


@pytest.fixture
def sophia_judge():
    """Create SOPHIA judge with mock components."""
    depth_analyzer = ContextDepthAnalyzer()
    return SophiaJudge(
        depth_analyzer=depth_analyzer,
    )


@pytest.fixture
def dike_judge():
    """Create DIKĒ judge."""
    return DikeJudge()


@pytest.fixture
def tribunal(veritas_judge, sophia_judge, dike_judge):
    """Create full tribunal with all judges."""
    return EnsembleArbiter(
        judges=[veritas_judge, sophia_judge, dike_judge],
        use_resilience=True,
    )


# ============================================================================
# Test Base Classes
# ============================================================================

class TestEvidence:
    """Test Evidence dataclass."""

    def test_create_evidence(self):
        """Test evidence creation."""
        evidence = Evidence(
            source="test_source",
            content="Test content",
            relevance=0.8,
            verified=True,
        )
        assert evidence.source == "test_source"
        assert evidence.content == "Test content"
        assert evidence.relevance == 0.8
        assert evidence.verified is True

    def test_evidence_relevance_validation(self):
        """Test relevance must be in range."""
        with pytest.raises(ValueError):
            Evidence(source="test", content="test", relevance=1.5)


class TestJudgeVerdict:
    """Test JudgeVerdict model."""

    def test_create_verdict(self):
        """Test verdict creation."""
        verdict = JudgeVerdict(
            judge_name="VERITAS",
            pillar="Truth",
            verdict=VerdictType.PASS,
            passed=True,
            confidence=0.85,
            reasoning="Test passed",
        )
        assert verdict.judge_name == "VERITAS"
        assert verdict.passed is True
        assert verdict.confidence == 0.85

    def test_abstained_factory(self):
        """Test abstained verdict factory."""
        verdict = JudgeVerdict.abstained(
            judge_name="SOPHIA",
            pillar="Wisdom",
            reason="Timeout",
        )
        assert verdict.is_abstained is True
        assert verdict.confidence == 0.0
        assert verdict.verdict == VerdictType.ABSTAIN

    def test_weighted_score(self):
        """Test weighted score calculation."""
        passed_verdict = JudgeVerdict(
            judge_name="TEST",
            pillar="Test",
            verdict=VerdictType.PASS,
            passed=True,
            confidence=0.8,
            reasoning="Test",
        )
        assert passed_verdict.weighted_score == 0.8

        failed_verdict = JudgeVerdict(
            judge_name="TEST",
            pillar="Test",
            verdict=VerdictType.FAIL,
            passed=False,
            confidence=0.8,
            reasoning="Test",
        )
        assert failed_verdict.weighted_score == 0.0


# ============================================================================
# Test VERITAS Judge
# ============================================================================

class TestVeritasJudge:
    """Test VERITAS (Truth Judge)."""

    @pytest.mark.asyncio
    async def test_veritas_properties(self, veritas_judge):
        """Test VERITAS properties."""
        assert veritas_judge.name == "VERITAS"
        assert veritas_judge.pillar == "Truth"
        assert veritas_judge.weight == 0.40

    @pytest.mark.asyncio
    async def test_veritas_passing_execution(
        self, veritas_judge, execution_log_passing
    ):
        """Test VERITAS passes valid execution."""
        verdict = await veritas_judge.evaluate(execution_log_passing)

        assert verdict.judge_name == "VERITAS"
        assert verdict.pillar == "Truth"
        # With mock providers, should generally pass
        assert verdict.confidence > 0.0

    @pytest.mark.asyncio
    async def test_veritas_detects_hallucination_markers(
        self, veritas_judge, execution_log_failing_truth
    ):
        """Test VERITAS detects hallucination markers."""
        verdict = await veritas_judge.evaluate(execution_log_failing_truth)

        # Should find hallucination markers
        marker_evidence = [
            e for e in verdict.evidence
            if "hallucination" in e.content.lower()
        ]
        assert len(marker_evidence) > 0

    @pytest.mark.asyncio
    async def test_veritas_health_check(self, veritas_judge):
        """Test VERITAS health check."""
        health = await veritas_judge.health_check()
        assert health["healthy"] is True
        assert health["name"] == "VERITAS"


# ============================================================================
# Test SOPHIA Judge
# ============================================================================

class TestSophiaJudge:
    """Test SOPHIA (Wisdom Judge)."""

    @pytest.mark.asyncio
    async def test_sophia_properties(self, sophia_judge):
        """Test SOPHIA properties."""
        assert sophia_judge.name == "SOPHIA"
        assert sophia_judge.pillar == "Wisdom"
        assert sophia_judge.weight == 0.30

    @pytest.mark.asyncio
    async def test_sophia_passing_execution(
        self, sophia_judge, execution_log_passing
    ):
        """Test SOPHIA passes execution with deep reasoning."""
        verdict = await sophia_judge.evaluate(execution_log_passing)

        assert verdict.judge_name == "SOPHIA"
        # Should pass due to good reasoning chain
        assert "depth" in str(verdict.metadata).lower() or verdict.passed

    @pytest.mark.asyncio
    async def test_sophia_detects_shallow_patterns(
        self, sophia_judge, execution_log_failing_wisdom
    ):
        """Test SOPHIA detects shallow/generic responses."""
        verdict = await sophia_judge.evaluate(execution_log_failing_wisdom)

        # Should detect shallow patterns
        assert verdict.metadata.get("shallow_score", 0) > 0 or not verdict.passed

    @pytest.mark.asyncio
    async def test_sophia_health_check(self, sophia_judge):
        """Test SOPHIA health check."""
        health = await sophia_judge.health_check()
        assert health["healthy"] is True
        assert health["name"] == "SOPHIA"


# ============================================================================
# Test DIKĒ Judge
# ============================================================================

class TestDikeJudge:
    """Test DIKĒ (Justice Judge)."""

    @pytest.mark.asyncio
    async def test_dike_properties(self, dike_judge):
        """Test DIKĒ properties."""
        assert dike_judge.name == "DIKĒ"
        assert dike_judge.pillar == "Justice"
        assert dike_judge.weight == 0.30

    @pytest.mark.asyncio
    async def test_dike_passing_execution(
        self, dike_judge, execution_log_passing
    ):
        """Test DIKĒ passes execution within role."""
        verdict = await dike_judge.evaluate(execution_log_passing)

        assert verdict.judge_name == "DIKĒ"
        # Analyzer analyzing = within role
        assert verdict.passed is True

    @pytest.mark.asyncio
    async def test_dike_detects_role_violation(
        self, dike_judge, execution_log_failing_justice
    ):
        """Test DIKĒ detects role violations."""
        verdict = await dike_judge.evaluate(execution_log_failing_justice)

        # Planner executing = role violation
        assert verdict.passed is False
        assert "role" in verdict.reasoning.lower() or "role_check" in str(verdict.metadata)

    @pytest.mark.asyncio
    async def test_dike_detects_constitutional_violation(
        self, dike_judge, execution_log_capital_offense
    ):
        """Test DIKĒ detects constitutional violations."""
        verdict = await dike_judge.evaluate(execution_log_capital_offense)

        # Should detect constitutional violations
        assert verdict.passed is False
        offense_level = verdict.metadata.get("offense_level", "none")
        assert offense_level == "capital"

    @pytest.mark.asyncio
    async def test_dike_role_extraction(self, dike_judge):
        """Test role extraction from agent_id."""
        assert dike_judge._extract_role("planner-001") == "planner"
        assert dike_judge._extract_role("executor-prod-002") == "executor"
        assert dike_judge._extract_role("analyzer-team-a") == "analyzer"
        assert dike_judge._extract_role("unknown-agent") == "unknown"


# ============================================================================
# Test Circuit Breaker
# ============================================================================

class TestCircuitBreaker:
    """Test circuit breaker pattern."""

    def test_initial_state_closed(self):
        """Test circuit starts closed."""
        breaker = CircuitBreaker()
        assert breaker.state == CircuitState.CLOSED
        assert not breaker.is_open()

    def test_opens_after_failures(self):
        """Test circuit opens after threshold failures."""
        breaker = CircuitBreaker(failure_threshold=3)

        breaker.record_failure()
        assert breaker.state == CircuitState.CLOSED

        breaker.record_failure()
        assert breaker.state == CircuitState.CLOSED

        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN
        assert breaker.is_open()

    def test_success_resets_failures(self):
        """Test success resets failure count."""
        breaker = CircuitBreaker(failure_threshold=3)

        breaker.record_failure()
        breaker.record_failure()
        breaker.record_success()

        # Should not open now even with more failures
        breaker.record_failure()
        assert breaker.state == CircuitState.CLOSED

    def test_half_open_after_timeout(self):
        """Test circuit goes half-open after recovery timeout."""
        breaker = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout=0.1,  # Very short for testing
        )

        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

        # Wait for recovery
        import time
        time.sleep(0.2)

        assert breaker.state == CircuitState.HALF_OPEN


# ============================================================================
# Test Resilient Judge Wrapper
# ============================================================================

class TestResilientJudgeWrapper:
    """Test resilient judge wrapper."""

    @pytest.mark.asyncio
    async def test_wrapper_passes_through_verdict(self, veritas_judge, execution_log_passing):
        """Test wrapper passes through normal verdict."""
        wrapper = ResilientJudgeWrapper(veritas_judge)

        verdict = await wrapper.evaluate(execution_log_passing)

        assert verdict.judge_name == "VERITAS"
        assert not verdict.is_abstained

    @pytest.mark.asyncio
    async def test_wrapper_abstains_on_circuit_open(self, veritas_judge, execution_log_passing):
        """Test wrapper abstains when circuit is open."""
        wrapper = ResilientJudgeWrapper(veritas_judge)

        # Force circuit open
        wrapper._circuit._state = CircuitState.OPEN

        verdict = await wrapper.evaluate(execution_log_passing)

        assert verdict.is_abstained
        assert "circuit breaker" in verdict.reasoning.lower()

    @pytest.mark.asyncio
    async def test_wrapper_stats(self, veritas_judge, execution_log_passing):
        """Test wrapper statistics tracking."""
        wrapper = ResilientJudgeWrapper(veritas_judge)

        await wrapper.evaluate(execution_log_passing)
        await wrapper.evaluate(execution_log_passing)

        stats = wrapper.get_stats()
        assert stats["calls"] == 2
        assert stats["successes"] == 2


# ============================================================================
# Test Ensemble Arbiter
# ============================================================================

class TestEnsembleArbiter:
    """Test ensemble arbiter."""

    @pytest.mark.asyncio
    async def test_arbiter_deliberation(self, tribunal, execution_log_passing):
        """Test full tribunal deliberation."""
        verdict = await tribunal.deliberate(execution_log_passing)

        assert isinstance(verdict, TribunalVerdict)
        assert verdict.decision in TribunalDecision
        assert 0.0 <= verdict.consensus_score <= 1.0
        assert len(verdict.individual_verdicts) == 3  # All 3 judges

    @pytest.mark.asyncio
    async def test_arbiter_detects_capital_offense(
        self, tribunal, execution_log_capital_offense
    ):
        """Test arbiter handles capital offense."""
        verdict = await tribunal.deliberate(execution_log_capital_offense)

        # Should detect capital offense
        assert verdict.offense_level == "capital" or verdict.decision == TribunalDecision.FAIL

    @pytest.mark.asyncio
    async def test_arbiter_health_check(self, tribunal):
        """Test arbiter health check."""
        health = await tribunal.health_check()
        assert health["healthy"] is True
        assert "judges" in health
        assert len(health["judges"]) == 3

    @pytest.mark.asyncio
    async def test_arbiter_stats(self, tribunal, execution_log_passing):
        """Test arbiter statistics."""
        await tribunal.deliberate(execution_log_passing)

        stats = tribunal.get_stats()
        assert stats["deliberation_count"] == 1


# ============================================================================
# Test Penal Registry
# ============================================================================

class TestPenalRegistry:
    """Test penal registry."""

    @pytest.mark.asyncio
    async def test_punish_agent(self):
        """Test punishing an agent."""
        registry = PenalRegistry()

        record = await registry.punish(
            agent_id="test-agent-001",
            offense=OffenseType.ROLE_VIOLATION,
            status=PenalStatus.QUARANTINE,
            offense_details="Attempted unauthorized execution",
            duration=timedelta(hours=1),
        )

        assert record.agent_id == "test-agent-001"
        assert record.status == PenalStatus.QUARANTINE
        assert record.is_active

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test getting agent status."""
        registry = PenalRegistry()

        # No record initially
        status = await registry.get_status("unknown-agent")
        assert status is None

        # After punishment
        await registry.punish(
            agent_id="test-agent-002",
            offense=OffenseType.TRUTH_VIOLATION,
            status=PenalStatus.PROBATION,
        )

        status = await registry.get_status("test-agent-002")
        assert status is not None
        assert status.status == PenalStatus.PROBATION

    @pytest.mark.asyncio
    async def test_pardon_agent(self):
        """Test pardoning an agent."""
        registry = PenalRegistry()

        await registry.punish(
            agent_id="test-agent-003",
            offense=OffenseType.WISDOM_VIOLATION,
            status=PenalStatus.WARNING,
        )

        # Pardon
        result = await registry.pardon("test-agent-003", reason="Good behavior")
        assert result is True

        # Should be cleared now
        status = await registry.get_status("test-agent-003")
        assert status is None

    @pytest.mark.asyncio
    async def test_escalation_on_repeat(self):
        """Test punishment escalation on repeat offense."""
        registry = PenalRegistry()

        # First offense
        record1 = await registry.punish(
            agent_id="repeat-offender",
            offense=OffenseType.ROLE_VIOLATION,
            status=PenalStatus.WARNING,
        )
        assert record1.offense_count == 1
        assert record1.status == PenalStatus.WARNING

        # Second offense - should escalate
        record2 = await registry.punish(
            agent_id="repeat-offender",
            offense=OffenseType.ROLE_VIOLATION,
            status=PenalStatus.WARNING,
        )
        assert record2.offense_count == 2
        assert record2.status == PenalStatus.PROBATION  # Escalated

    @pytest.mark.asyncio
    async def test_check_restrictions(self):
        """Test restriction checking."""
        registry = PenalRegistry()

        # No restrictions when clear
        result = await registry.check_restrictions("clear-agent", "execute")
        assert result["allowed"] is True

        # Quarantine restricts most actions
        await registry.punish(
            agent_id="quarantined-agent",
            offense=OffenseType.CONSTITUTIONAL_VIOLATION,
            status=PenalStatus.QUARANTINE,
        )

        result = await registry.check_restrictions("quarantined-agent", "execute")
        assert result["allowed"] is False

        # But allows re-education
        result = await registry.check_restrictions("quarantined-agent", "re_education")
        assert result["allowed"] is True


# ============================================================================
# Test Semantic Cache
# ============================================================================

class TestTieredSemanticCache:
    """Test tiered semantic cache."""

    @pytest.mark.asyncio
    async def test_cache_miss_and_compute(self):
        """Test cache miss triggers computation."""
        cache = TieredSemanticCache()

        async def mock_compute(text: str) -> float:
            return 0.5

        result = await cache.get_or_compute(
            text="Test text",
            compute_fn=mock_compute,
            mode=CacheMode.NORMAL,
        )

        assert result.hit is True  # L3 computed counts as hit
        assert result.entropy == 0.5

    @pytest.mark.asyncio
    async def test_l1_cache_hit(self):
        """Test L1 exact cache hit."""
        cache = TieredSemanticCache()

        async def mock_compute(text: str) -> float:
            return 0.5

        # First call
        await cache.get_or_compute("Exact text", mock_compute)

        # Second call should hit L1
        result = await cache.get_or_compute("Exact text", mock_compute)

        stats = cache.get_stats()
        assert stats["l1_hits"] > 0

    @pytest.mark.asyncio
    async def test_cache_stats(self):
        """Test cache statistics."""
        cache = TieredSemanticCache()

        async def mock_compute(text: str) -> float:
            return 0.5

        await cache.get_or_compute("Text 1", mock_compute)
        await cache.get_or_compute("Text 2", mock_compute)

        stats = cache.get_stats()
        assert stats["total_requests"] == 2
        assert stats["l3_computes"] == 2


# ============================================================================
# Integration Test - Full Pipeline
# ============================================================================

class TestFullPipeline:
    """Test complete tribunal pipeline."""

    @pytest.mark.asyncio
    async def test_full_pipeline_pass(self, tribunal, execution_log_passing):
        """Test full pipeline with passing execution."""
        verdict = await tribunal.deliberate(execution_log_passing)

        # Should pass or at least not fail completely
        assert verdict.decision in [
            TribunalDecision.PASS,
            TribunalDecision.REVIEW,
        ]

    @pytest.mark.asyncio
    async def test_full_pipeline_fail(self, tribunal, execution_log_capital_offense):
        """Test full pipeline with capital offense."""
        verdict = await tribunal.deliberate(execution_log_capital_offense)

        # Should fail or require review due to constitutional violation
        assert verdict.decision in [
            TribunalDecision.FAIL,
            TribunalDecision.CAPITAL,
            TribunalDecision.REVIEW,
        ]

        # Should recommend punishment
        if verdict.decision in [TribunalDecision.FAIL, TribunalDecision.CAPITAL]:
            assert verdict.punishment_recommendation is not None

    @pytest.mark.asyncio
    async def test_full_pipeline_with_punishment(self):
        """Test full pipeline including punishment registry."""
        # Create tribunal
        veritas = VeritasJudge(
            entropy_detector=SemanticEntropyDetector(),
            rag_verifier=RAGVerifier(),
        )
        sophia = SophiaJudge()
        dike = DikeJudge()
        tribunal = EnsembleArbiter(judges=[veritas, sophia, dike])

        # Create registry
        registry = PenalRegistry()

        # Execute bad action
        log = ExecutionLog(
            trace_id="pipeline-test",
            agent_id="planner-bad",
            task="Execute deployment",
            action="Executed and deployed the application",  # Planner executing
            outcome="Done",
            reasoning_trace="",
        )

        verdict = await tribunal.deliberate(log)

        # If failed, apply punishment
        if verdict.decision in [TribunalDecision.FAIL, TribunalDecision.CAPITAL]:
            record = await registry.punish(
                agent_id="planner-bad",
                offense=OffenseType.ROLE_VIOLATION,
                status=PenalStatus.QUARANTINE,
                duration=timedelta(hours=24),
            )

            # Verify punishment applied
            status = await registry.get_status("planner-bad")
            assert status is not None
            assert status.is_active
