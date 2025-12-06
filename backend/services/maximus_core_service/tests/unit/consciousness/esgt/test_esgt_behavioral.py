"""
Comprehensive Tests for ESGT Coordinator
=========================================

Tests for the Global Workspace Dynamics ignition protocol.
"""

import time
from unittest.mock import MagicMock, AsyncMock

import pytest

from consciousness.esgt.coordinator import ESGTCoordinator
from consciousness.esgt.enums import ESGTPhase, SalienceLevel
from consciousness.esgt.models import SalienceScore, TriggerConditions, ESGTEvent


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
            relevance=0.7,
            urgency=0.9,
        )
        
        assert score.novelty == 0.8
        assert score.urgency == 0.9

    def test_compute_total(self):
        """compute_total should return weighted sum."""
        score = SalienceScore(novelty=1.0, relevance=1.0, urgency=1.0, confidence=1.0)
        
        total = score.compute_total()
        
        assert 0 < total <= 1.0

    def test_get_level(self):
        """get_level should return SalienceLevel."""
        score = SalienceScore(novelty=0.8, relevance=0.8, urgency=0.9)
        
        level = score.get_level()
        
        assert isinstance(level, SalienceLevel)


# =============================================================================
# TRIGGER CONDITIONS TESTS
# =============================================================================


class TestTriggerConditions:
    """Test TriggerConditions data structure."""

    def test_default_values(self):
        """Default values should be sensible."""
        conditions = TriggerConditions()
        
        assert conditions.min_salience > 0
        assert conditions.max_tig_latency_ms > 0

    def test_check_salience(self):
        """check_salience should evaluate score."""
        conditions = TriggerConditions()
        score = SalienceScore(novelty=0.9, relevance=0.9, urgency=0.9)
        
        result = conditions.check_salience(score)
        
        assert isinstance(result, bool)


# =============================================================================
# ESGT EVENT TESTS
# =============================================================================


class TestESGTEvent:
    """Test ESGTEvent data structure."""

    def test_creation(self):
        """ESGTEvent should be creatable."""
        event = ESGTEvent(
            event_id="esgt-001",
            timestamp_start=time.time(),
            content={"data": "test"},
        )
        
        assert event.event_id == "esgt-001"

    def test_transition_phase(self):
        """transition_phase should record transition."""
        event = ESGTEvent(event_id="esgt-002", timestamp_start=time.time())
        
        event.transition_phase(ESGTPhase.PREPARE)
        
        assert event.current_phase == ESGTPhase.PREPARE
        assert len(event.phase_transitions) > 0

    def test_finalize(self):
        """finalize should mark event complete."""
        event = ESGTEvent(event_id="esgt-003", timestamp_start=time.time())
        
        event.finalize(success=True)
        
        assert event.success is True
        assert event.timestamp_end is not None


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
        
        assert coordinator.tig is mock_tig

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
        mock_tig.nodes = {}  # Dict, not list
        mock_tig.get_health_metrics = MagicMock(return_value={})
        
        coordinator = ESGTCoordinator(tig_fabric=mock_tig)
        
        # start is async, so we just verify it doesn't raise
        import asyncio
        asyncio.get_event_loop().run_until_complete(coordinator.start())
        
        assert coordinator._running is True
        
        asyncio.get_event_loop().run_until_complete(coordinator.stop())

    def test_stop(self):
        """Stop should clear running state."""
        mock_tig = MagicMock()
        mock_tig.nodes = {}  # Dict, not list
        mock_tig.get_health_metrics = MagicMock(return_value={})
        
        coordinator = ESGTCoordinator(tig_fabric=mock_tig)
        
        import asyncio
        asyncio.get_event_loop().run_until_complete(coordinator.start())
        asyncio.get_event_loop().run_until_complete(coordinator.stop())
        
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
