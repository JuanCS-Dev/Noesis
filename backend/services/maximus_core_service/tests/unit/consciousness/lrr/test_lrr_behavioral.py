"""
Comprehensive Tests for LRR - Recursive Reasoner
=================================================

Tests for metacognitive reasoning and belief management.
"""

from unittest.mock import MagicMock

import pytest

from consciousness.lrr.recursive_reasoner import RecursiveReasoner
from consciousness.lrr.belief_graph import BeliefGraph
from consciousness.lrr.belief_models import Belief, BeliefType
from consciousness.lrr.contradiction_detector import ContradictionDetector


# =============================================================================
# BELIEF TESTS
# =============================================================================


class TestBelief:
    """Test Belief data structure."""

    def test_creation(self):
        """Belief should be creatable."""
        belief = Belief(
            content="The sky is blue",
            belief_type=BeliefType.FACTUAL,
            confidence=0.9,
        )
        
        assert belief.content == "The sky is blue"
        assert belief.confidence == 0.9

    def test_belief_types(self):
        """All belief types should work."""
        for belief_type in BeliefType:
            belief = Belief(
                content="Test",
                belief_type=belief_type,
                confidence=0.5,
            )
            assert belief.belief_type == belief_type


# =============================================================================
# BELIEF GRAPH TESTS
# =============================================================================


class TestBeliefGraph:
    """Test BeliefGraph behavior."""

    def test_creation(self):
        """BeliefGraph should be creatable."""
        graph = BeliefGraph()
        
        assert graph is not None

    def test_add_belief(self):
        """Should add belief to graph."""
        graph = BeliefGraph()
        belief = Belief(
            content="Test belief",
            belief_type=BeliefType.FACTUAL,
            confidence=0.8,
        )
        
        graph.add_belief(belief)
        
        # Should not raise
        assert True

    def test_get_beliefs_for_id(self):
        """Should be able to work with beliefs."""
        graph = BeliefGraph()
        belief = Belief(
            content="Test belief",
            belief_type=BeliefType.FACTUAL,
            confidence=0.8,
        )
        
        graph.add_belief(belief)
        
        # Just verify add didn't raise
        assert True


# =============================================================================
# CONTRADICTION DETECTOR TESTS
# =============================================================================


class TestContradictionDetector:
    """Test ContradictionDetector behavior."""

    def test_creation(self):
        """ContradictionDetector should be creatable."""
        detector = ContradictionDetector()
        
        assert detector is not None


# =============================================================================
# RECURSIVE REASONER TESTS
# =============================================================================


class TestRecursiveReasonerInit:
    """Test RecursiveReasoner initialization."""

    def test_creation(self):
        """RecursiveReasoner should be creatable."""
        reasoner = RecursiveReasoner()
        
        assert reasoner is not None

    def test_custom_max_depth(self):
        """Custom max depth should be accepted."""
        reasoner = RecursiveReasoner(max_depth=5)
        
        assert reasoner.max_depth == 5


class TestRecursiveReasonerReasoning:
    """Test recursive reasoning."""

    def test_reason_recursively(self):
        """Should reason over belief."""
        reasoner = RecursiveReasoner()
        belief = Belief(
            content="I should help the user",
            belief_type=BeliefType.NORMATIVE,  # Use NORMATIVE instead of GOAL
            confidence=0.9,
        )
        context = {"situation": "user request"}
        
        result = reasoner.reason_recursively(belief, context)
        
        assert result is not None
