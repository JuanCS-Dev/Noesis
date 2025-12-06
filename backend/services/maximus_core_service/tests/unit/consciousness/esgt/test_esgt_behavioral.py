"""
Comprehensive Tests for ESGT Coordinator
=========================================

Tests for the Global Workspace Dynamics ignition protocol.
"""

from unittest.mock import MagicMock, AsyncMock

import pytest

from consciousness.esgt.coordinator import ESGTCoordinator, ESGTPhase
from consciousness.esgt.models import SalienceScore, SalienceLevel, TriggerConditions, ESGTEvent


# =============================================================================
# ESGT PHASE TESTS
# =============================================================================


class TestESGTPhase:
    """Test ESGTPhase enum."""

    def test_all_phases_exist(self):
        """All phases should exist."""
        assert ESGTPhase.PREPARE
        assert ESGTPhase.SYNCHRONIZE
        assert ESGTPhase.BROADCAST
        assert ESGTPhase.SUSTAIN
        assert ESGTPhase.DISSOLVE


# =============================================================================
# SALIENCE SCORE TESTS
# =============================================================================


class TestSalienceScore:
    """Test SalienceScore data structure."""

    def test_creation(self):
        """SalienceScore should be creatable."""
        score = SalienceScore(
            novelty=0.8,
            emotional_relevance=0.7,
            goal_relevance=0.6,
            urgency=0.9,
        )
        
        assert score.novelty == 0.8
        assert score.urgency == 0.9


# =============================================================================
# TRIGGER CONDITIONS TESTS
# =============================================================================


class TestTriggerConditions:
    """Test TriggerConditions data structure."""

    def test_default_values(self):
        """Default values should be sensible."""
        conditions = TriggerConditions()
        
        assert conditions.min_salience > 0
        assert conditions.min_coherence > 0


# =============================================================================
# ESGT EVENT TESTS
# =============================================================================


class TestESGTEvent:
    """Test ESGTEvent data structure."""

    def test_creation(self):
        """ESGTEvent should be creatable."""
        event = ESGTEvent(
            event_id="esgt-001",
            content={"data": "test"},
            salience=SalienceScore(0.8, 0.7, 0.6, 0.9),
        )
        
        assert event.event_id == "esgt-001"


# =============================================================================
# ESGT COORDINATOR INIT TESTS
# =============================================================================


class TestESGTCoordinatorInit:
    """Test ESGTCoordinator initialization."""

    def test_creation_with_tig(self):
        """Coordinator should accept TIG fabric."""
        mock_tig = MagicMock()
        mock_tig.nodes = []
        mock_tig.get_health_metrics = MagicMock(return_value={})
        
        coordinator = ESGTCoordinator(tig_fabric=mock_tig)
        
        assert coordinator.tig_fabric is mock_tig

    def test_custom_coordinator_id(self):
        """Custom coordinator ID should be accepted."""
        mock_tig = MagicMock()
        mock_tig.nodes = []
        mock_tig.get_health_metrics = MagicMock(return_value={})
        
        coordinator = ESGTCoordinator(tig_fabric=mock_tig, coordinator_id="custom-esgt")
        
        assert coordinator.coordinator_id == "custom-esgt"


class TestESGTCoordinatorLifecycle:
    """Test start/stop lifecycle."""

    def test_start(self):
        """Start should set running state."""
        mock_tig = MagicMock()
        mock_tig.nodes = []
        mock_tig.get_health_metrics = MagicMock(return_value={})
        
        coordinator = ESGTCoordinator(tig_fabric=mock_tig)
        
        coordinator.start()
        
        assert coordinator._running is True
        
        coordinator.stop()

    def test_stop(self):
        """Stop should clear running state."""
        mock_tig = MagicMock()
        mock_tig.nodes = []
        mock_tig.get_health_metrics = MagicMock(return_value={})
        
        coordinator = ESGTCoordinator(tig_fabric=mock_tig)
        
        coordinator.start()
        coordinator.stop()
        
        assert coordinator._running is False


class TestESGTCoordinatorRepr:
    """Test string representation."""

    def test_repr(self):
        """Repr should include coordinator info."""
        mock_tig = MagicMock()
        mock_tig.nodes = []
        mock_tig.get_health_metrics = MagicMock(return_value={})
        
        coordinator = ESGTCoordinator(tig_fabric=mock_tig)
        
        repr_str = repr(coordinator)
        
        assert "ESGT" in repr_str or "Coordinator" in repr_str
