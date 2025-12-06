"""
Comprehensive tests for LRR models (belief_models, contradiction_models, reasoning_models)

Tests cover:
- BeliefType, ContradictionType, ResolutionStrategy enums
- Belief dataclass with validation, negation detection, hashing
- Contradiction dataclass
- Resolution dataclass
- ReasoningStep, ReasoningLevel, RecursiveReasoningResult dataclasses
"""

from datetime import datetime
from uuid import UUID

import pytest

from consciousness.lrr.belief_models import (
    Belief,
    BeliefType,
    ContradictionType,
    ResolutionStrategy,
)
from consciousness.lrr.contradiction_models import Contradiction, Resolution
from consciousness.lrr.reasoning_models import (
    ReasoningLevel,
    ReasoningStep,
    RecursiveReasoningResult,
)


# ==================== BELIEF MODELS TESTS ====================


class TestBeliefType:
    """Test BeliefType enum."""

    def test_all_belief_types_exist(self):
        """Test that all expected belief types are defined."""
        assert BeliefType.FACTUAL.value == "factual"
        assert BeliefType.META.value == "meta"
        assert BeliefType.NORMATIVE.value == "normative"
        assert BeliefType.EPISTEMIC.value == "epistemic"

    def test_belief_type_count(self):
        """Test that we have all expected belief types."""
        assert len(BeliefType) == 4


class TestContradictionType:
    """Test ContradictionType enum."""

    def test_all_contradiction_types_exist(self):
        """Test that all expected contradiction types are defined."""
        assert ContradictionType.DIRECT.value == "direct"
        assert ContradictionType.TRANSITIVE.value == "transitive"
        assert ContradictionType.TEMPORAL.value == "temporal"
        assert ContradictionType.CONTEXTUAL.value == "contextual"

    def test_contradiction_type_count(self):
        """Test that we have all expected contradiction types."""
        assert len(ContradictionType) == 4


class TestResolutionStrategy:
    """Test ResolutionStrategy enum."""

    def test_all_resolution_strategies_exist(self):
        """Test that all expected resolution strategies are defined."""
        assert ResolutionStrategy.RETRACT_WEAKER.value == "retract_weaker"
        assert ResolutionStrategy.WEAKEN_BOTH.value == "weaken_both"
        assert ResolutionStrategy.CONTEXTUALIZE.value == "contextualize"
        assert ResolutionStrategy.TEMPORIZE.value == "temporize"
        assert ResolutionStrategy.HITL_ESCALATE.value == "hitl_escalate"

    def test_resolution_strategy_count(self):
        """Test that we have all expected resolution strategies."""
        assert len(ResolutionStrategy) == 5


class TestBelief:
    """Test Belief dataclass."""

    def test_creation_minimal(self):
        """Test creating belief with minimal required fields."""
        belief = Belief(content="The sky is blue")

        assert belief.content == "The sky is blue"
        assert belief.belief_type == BeliefType.FACTUAL
        assert belief.confidence == 0.5
        assert belief.meta_level == 0
        assert isinstance(belief.id, UUID)
        assert belief.justification == []
        assert belief.context == {}

    def test_creation_complete(self):
        """Test creating belief with all fields."""
        now = datetime.now()
        justification_belief = Belief(content="Weather report says so")

        belief = Belief(
            content="It will rain tomorrow",
            belief_type=BeliefType.FACTUAL,
            confidence=0.8,
            justification=[justification_belief],
            context={"location": "São Paulo"},
            timestamp=now,
            meta_level=1,
        )

        assert belief.content == "It will rain tomorrow"
        assert belief.belief_type == BeliefType.FACTUAL
        assert belief.confidence == 0.8
        assert len(belief.justification) == 1
        assert belief.context["location"] == "São Paulo"
        assert belief.timestamp == now
        assert belief.meta_level == 1

    def test_confidence_validation_too_low(self):
        """Test that confidence < 0 raises ValueError."""
        with pytest.raises(ValueError, match="Confidence must be"):
            Belief(content="Test", confidence=-0.1)

    def test_confidence_validation_too_high(self):
        """Test that confidence > 1 raises ValueError."""
        with pytest.raises(ValueError, match="Confidence must be"):
            Belief(content="Test", confidence=1.1)

    def test_confidence_boundaries(self):
        """Test that confidence at boundaries (0.0, 1.0) is valid."""
        belief_min = Belief(content="Test", confidence=0.0)
        belief_max = Belief(content="Test", confidence=1.0)

        assert belief_min.confidence == 0.0
        assert belief_max.confidence == 1.0

    def test_meta_level_validation_negative(self):
        """Test that negative meta_level raises ValueError."""
        with pytest.raises(ValueError, match="Meta level must be"):
            Belief(content="Test", meta_level=-1)

    def test_meta_level_valid_values(self):
        """Test that various valid meta_levels work."""
        for level in [0, 1, 2, 5, 10]:
            belief = Belief(content="Test", meta_level=level)
            assert belief.meta_level == level

    def test_hash_and_equality(self):
        """Test that beliefs can be hashed and compared by ID."""
        belief1 = Belief(content="Test")
        belief2 = Belief(content="Test")
        belief3 = belief1

        # Different beliefs should not be equal even with same content
        assert belief1 != belief2
        # Same belief should be equal
        assert belief1 == belief3
        # Should be hashable
        assert isinstance(hash(belief1), int)
        # Can be used in sets
        belief_set = {belief1, belief2, belief3}
        assert len(belief_set) == 2  # belief1 and belief3 are same

    def test_equality_with_non_belief(self):
        """Test that belief equality with non-Belief returns False."""
        belief = Belief(content="Test")
        assert belief != "Test"
        assert belief != 123
        assert belief != None

    def test_is_negation_of_simple_not(self):
        """Test negation detection with 'not'."""
        belief1 = Belief(content="The IP is malicious")
        belief2 = Belief(content="The IP is not malicious")

        assert belief1.is_negation_of(belief2)
        assert belief2.is_negation_of(belief1)

    def test_is_negation_of_isnt(self):
        """Test negation detection with 'isn't'."""
        belief1 = Belief(content="Action is ethical")
        belief2 = Belief(content="Action isn't ethical")

        assert belief1.is_negation_of(belief2)
        assert belief2.is_negation_of(belief1)

    def test_is_negation_of_different_types(self):
        """Test that beliefs of different types are not negations."""
        belief1 = Belief(content="IP is safe", belief_type=BeliefType.FACTUAL)
        belief2 = Belief(content="IP is not safe", belief_type=BeliefType.META)

        assert not belief1.is_negation_of(belief2)

    def test_is_negation_of_completely_different(self):
        """Test that completely different beliefs are not negations."""
        belief1 = Belief(content="The sky is blue")
        belief2 = Belief(content="The grass is green")

        assert not belief1.is_negation_of(belief2)

    def test_is_negation_of_with_logical_symbols(self):
        """Test negation detection with logical symbols."""
        belief1 = Belief(content="A is true")
        belief2 = Belief(content="¬A is true")

        assert belief1.is_negation_of(belief2)

    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        result = Belief._normalize_whitespace("  too   many    spaces  ")
        assert result == "too many spaces"

    def test_strip_negations(self):
        """Test stripping negation markers."""
        result = Belief.strip_negations("The IP is not malicious")
        assert "not" not in result.lower()

        result2 = Belief.strip_negations("Action isn't ethical")
        assert "isn't" not in result2.lower()
        assert "is" in result2.lower()

    def test_belief_with_justification_chain(self):
        """Test creating belief with chain of justifications."""
        base_belief = Belief(content="Weather forecast says rain")
        mid_belief = Belief(
            content="It will probably rain", justification=[base_belief]
        )
        top_belief = Belief(
            content="I should bring umbrella", justification=[mid_belief]
        )

        assert len(top_belief.justification) == 1
        assert top_belief.justification[0] == mid_belief
        assert len(mid_belief.justification) == 1
        assert mid_belief.justification[0] == base_belief


# ==================== CONTRADICTION MODELS TESTS ====================


class TestContradiction:
    """Test Contradiction dataclass."""

    def test_creation_minimal(self):
        """Test creating contradiction with minimal fields."""
        belief_a = Belief(content="IP is safe")
        belief_b = Belief(content="IP is not safe")

        contradiction = Contradiction(
            belief_a=belief_a,
            belief_b=belief_b,
            contradiction_type=ContradictionType.DIRECT,
        )

        assert contradiction.belief_a == belief_a
        assert contradiction.belief_b == belief_b
        assert contradiction.contradiction_type == ContradictionType.DIRECT
        assert contradiction.severity == 1.0
        assert contradiction.suggested_resolution == ResolutionStrategy.RETRACT_WEAKER
        assert isinstance(contradiction.id, UUID)
        # Explanation should be auto-generated
        assert "Contradiction detected" in contradiction.explanation

    def test_creation_complete(self):
        """Test creating contradiction with all fields."""
        belief_a = Belief(content="Action is ethical")
        belief_b = Belief(content="Action is unethical")

        contradiction = Contradiction(
            belief_a=belief_a,
            belief_b=belief_b,
            contradiction_type=ContradictionType.TEMPORAL,
            severity=0.8,
            explanation="Custom explanation of the contradiction",
            suggested_resolution=ResolutionStrategy.CONTEXTUALIZE,
        )

        assert contradiction.severity == 0.8
        assert contradiction.explanation == "Custom explanation of the contradiction"
        assert contradiction.suggested_resolution == ResolutionStrategy.CONTEXTUALIZE

    def test_auto_generated_explanation(self):
        """Test that explanation is auto-generated when not provided."""
        belief_a = Belief(content="First belief")
        belief_b = Belief(content="Second belief")

        contradiction = Contradiction(
            belief_a=belief_a,
            belief_b=belief_b,
            contradiction_type=ContradictionType.TRANSITIVE,
        )

        assert "First belief" in contradiction.explanation
        assert "Second belief" in contradiction.explanation
        assert "transitive" in contradiction.explanation.lower()

    def test_all_contradiction_types(self):
        """Test creating contradictions with all types."""
        belief_a = Belief(content="A")
        belief_b = Belief(content="B")

        for ctype in ContradictionType:
            contradiction = Contradiction(
                belief_a=belief_a, belief_b=belief_b, contradiction_type=ctype
            )
            assert contradiction.contradiction_type == ctype
            assert ctype.value in contradiction.explanation


class TestResolution:
    """Test Resolution dataclass."""

    def test_creation_minimal(self):
        """Test creating resolution with minimal fields."""
        belief_a = Belief(content="A")
        belief_b = Belief(content="B")
        contradiction = Contradiction(
            belief_a=belief_a,
            belief_b=belief_b,
            contradiction_type=ContradictionType.DIRECT,
        )

        resolution = Resolution(
            contradiction=contradiction, strategy=ResolutionStrategy.RETRACT_WEAKER
        )

        assert resolution.contradiction == contradiction
        assert resolution.strategy == ResolutionStrategy.RETRACT_WEAKER
        assert resolution.beliefs_modified == []
        assert resolution.beliefs_removed == []
        assert resolution.new_beliefs == []
        assert isinstance(resolution.timestamp, datetime)
        assert isinstance(resolution.id, UUID)

    def test_creation_complete(self):
        """Test creating resolution with all fields."""
        belief_a = Belief(content="A", confidence=0.3)
        belief_b = Belief(content="B", confidence=0.8)
        contradiction = Contradiction(
            belief_a=belief_a,
            belief_b=belief_b,
            contradiction_type=ContradictionType.DIRECT,
        )

        # Modify weaker belief
        modified_belief = Belief(content="A", confidence=0.1)
        new_belief = Belief(content="C - contextualized")

        resolution = Resolution(
            contradiction=contradiction,
            strategy=ResolutionStrategy.WEAKEN_BOTH,
            beliefs_modified=[modified_belief],
            beliefs_removed=[belief_a],
            new_beliefs=[new_belief],
        )

        assert len(resolution.beliefs_modified) == 1
        assert len(resolution.beliefs_removed) == 1
        assert len(resolution.new_beliefs) == 1
        assert resolution.beliefs_modified[0] == modified_belief
        assert resolution.new_beliefs[0] == new_belief

    def test_all_resolution_strategies(self):
        """Test creating resolutions with all strategies."""
        belief_a = Belief(content="A")
        belief_b = Belief(content="B")
        contradiction = Contradiction(
            belief_a=belief_a,
            belief_b=belief_b,
            contradiction_type=ContradictionType.DIRECT,
        )

        for strategy in ResolutionStrategy:
            resolution = Resolution(contradiction=contradiction, strategy=strategy)
            assert resolution.strategy == strategy


# ==================== REASONING MODELS TESTS ====================


class TestReasoningStep:
    """Test ReasoningStep dataclass."""

    def test_creation_minimal(self):
        """Test creating reasoning step with minimal fields."""
        belief = Belief(content="Test belief")

        step = ReasoningStep(belief=belief, meta_level=0)

        assert step.belief == belief
        assert step.meta_level == 0
        assert step.justification_chain == []
        assert step.confidence_assessment == 0.5
        assert isinstance(step.timestamp, datetime)

    def test_creation_complete(self):
        """Test creating reasoning step with all fields."""
        belief = Belief(content="Conclusion")
        j1 = Belief(content="Premise 1")
        j2 = Belief(content="Premise 2")

        step = ReasoningStep(
            belief=belief,
            meta_level=1,
            justification_chain=[j1, j2],
            confidence_assessment=0.85,
        )

        assert len(step.justification_chain) == 2
        assert step.confidence_assessment == 0.85
        assert step.meta_level == 1

    def test_multi_level_reasoning(self):
        """Test reasoning steps at different meta levels."""
        for level in [0, 1, 2, 3]:
            belief = Belief(content=f"Level {level} belief", meta_level=level)
            step = ReasoningStep(belief=belief, meta_level=level)
            assert step.meta_level == level


class TestReasoningLevel:
    """Test ReasoningLevel dataclass."""

    def test_creation_minimal(self):
        """Test creating reasoning level with minimal fields."""
        level = ReasoningLevel(level=0)

        assert level.level == 0
        assert level.beliefs == []
        assert level.coherence == 1.0
        assert level.steps == []

    def test_creation_complete(self):
        """Test creating reasoning level with all fields."""
        b1 = Belief(content="Belief 1")
        b2 = Belief(content="Belief 2")
        s1 = ReasoningStep(belief=b1, meta_level=0)
        s2 = ReasoningStep(belief=b2, meta_level=0)

        level = ReasoningLevel(
            level=1, beliefs=[b1, b2], coherence=0.9, steps=[s1, s2]
        )

        assert level.level == 1
        assert len(level.beliefs) == 2
        assert level.coherence == 0.9
        assert len(level.steps) == 2

    def test_multiple_levels(self):
        """Test creating multiple reasoning levels."""
        levels = []
        for i in range(3):
            belief = Belief(content=f"Level {i} belief", meta_level=i)
            step = ReasoningStep(belief=belief, meta_level=i)
            level = ReasoningLevel(level=i, beliefs=[belief], steps=[step])
            levels.append(level)

        assert len(levels) == 3
        assert levels[0].level == 0
        assert levels[2].level == 2


class TestRecursiveReasoningResult:
    """Test RecursiveReasoningResult dataclass."""

    def test_creation_minimal(self):
        """Test creating reasoning result with minimal fields."""
        level0 = ReasoningLevel(level=0)

        result = RecursiveReasoningResult(
            levels=[level0], final_depth=0, coherence_score=1.0
        )

        assert len(result.levels) == 1
        assert result.final_depth == 0
        assert result.coherence_score == 1.0
        assert result.contradictions_detected == []
        assert result.resolutions_applied == []
        assert isinstance(result.timestamp, datetime)
        assert result.duration_ms == 0.0

    def test_creation_complete(self):
        """Test creating reasoning result with all fields."""
        # Create beliefs
        b1 = Belief(content="Base belief")
        b2 = Belief(content="Meta belief")

        # Create contradiction
        contradiction = Contradiction(
            belief_a=b1, belief_b=b2, contradiction_type=ContradictionType.DIRECT
        )

        # Create resolution
        resolution = Resolution(
            contradiction=contradiction, strategy=ResolutionStrategy.RETRACT_WEAKER
        )

        # Create levels
        level0 = ReasoningLevel(level=0, beliefs=[b1])
        level1 = ReasoningLevel(level=1, beliefs=[b2])

        result = RecursiveReasoningResult(
            levels=[level0, level1],
            final_depth=1,
            coherence_score=0.85,
            contradictions_detected=[contradiction],
            resolutions_applied=[resolution],
            duration_ms=125.5,
        )

        assert len(result.levels) == 2
        assert result.final_depth == 1
        assert result.coherence_score == 0.85
        assert len(result.contradictions_detected) == 1
        assert len(result.resolutions_applied) == 1
        assert result.duration_ms == 125.5

    def test_deep_reasoning_hierarchy(self):
        """Test creating deep reasoning hierarchy."""
        levels = []
        for i in range(5):
            belief = Belief(content=f"Level {i} belief", meta_level=i)
            level = ReasoningLevel(level=i, beliefs=[belief], coherence=0.9 - i * 0.1)
            levels.append(level)

        result = RecursiveReasoningResult(
            levels=levels, final_depth=4, coherence_score=0.75
        )

        assert len(result.levels) == 5
        assert result.final_depth == 4
        assert result.levels[0].coherence == 0.9
        assert result.levels[4].coherence == 0.5

    def test_optional_integration_fields(self):
        """Test that optional integration fields are None by default."""
        level0 = ReasoningLevel(level=0)
        result = RecursiveReasoningResult(
            levels=[level0], final_depth=0, coherence_score=1.0
        )

        assert result.meta_report is None
        assert result.introspection_report is None
        assert result.attention_state is None
        assert result.boundary_assessment is None
        assert result.self_summary is None
        assert result.episodic_episode is None
        assert result.episodic_narrative is None
        assert result.episodic_coherence is None


# ==================== INTEGRATION TESTS ====================


class TestIntegration:
    """Test integration between different model types."""

    def test_belief_contradiction_resolution_flow(self):
        """Test complete flow from beliefs to contradiction to resolution."""
        # Create conflicting beliefs
        belief_a = Belief(content="System is secure", confidence=0.6)
        belief_b = Belief(content="System is not secure", confidence=0.8)

        # Detect contradiction
        contradiction = Contradiction(
            belief_a=belief_a,
            belief_b=belief_b,
            contradiction_type=ContradictionType.DIRECT,
            severity=0.9,
        )

        # Apply resolution
        resolution = Resolution(
            contradiction=contradiction,
            strategy=ResolutionStrategy.RETRACT_WEAKER,
            beliefs_removed=[belief_a],  # Remove weaker belief
        )

        assert resolution.contradiction == contradiction
        assert len(resolution.beliefs_removed) == 1
        assert resolution.beliefs_removed[0] == belief_a

    def test_reasoning_hierarchy_with_contradictions(self):
        """Test reasoning hierarchy that detects contradictions."""
        # Level 0: Object-level beliefs
        b1 = Belief(content="IP 1.2.3.4 is malicious", meta_level=0)
        b2 = Belief(content="IP 1.2.3.4 is safe", meta_level=0)

        # Create contradiction
        contradiction = Contradiction(
            belief_a=b1, belief_b=b2, contradiction_type=ContradictionType.DIRECT
        )

        # Create resolution
        resolution = Resolution(
            contradiction=contradiction, strategy=ResolutionStrategy.HITL_ESCALATE
        )

        # Level 1: Meta-level reflection
        b3 = Belief(
            content="I have contradictory beliefs about IP 1.2.3.4",
            meta_level=1,
            justification=[b1, b2],
        )

        # Create reasoning levels
        level0 = ReasoningLevel(level=0, beliefs=[b1, b2], coherence=0.3)
        level1 = ReasoningLevel(level=1, beliefs=[b3], coherence=0.9)

        result = RecursiveReasoningResult(
            levels=[level0, level1],
            final_depth=1,
            coherence_score=0.6,
            contradictions_detected=[contradiction],
            resolutions_applied=[resolution],
        )

        assert result.final_depth == 1
        assert len(result.contradictions_detected) == 1
        assert len(result.resolutions_applied) == 1
        assert result.levels[0].coherence < result.levels[1].coherence
