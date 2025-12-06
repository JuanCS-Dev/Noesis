"""
Comprehensive Tests for Reactive Fabric - Event Collection
===========================================================

Tests for consciousness event collection and processing.
"""

from unittest.mock import MagicMock, AsyncMock

import pytest

from consciousness.reactive_fabric.collectors.event_collector import (
    EventCollector,
    EventType,
    EventSeverity,
    ConsciousnessEvent,
)


# =============================================================================
# EVENT TYPE TESTS
# =============================================================================


class TestEventType:
    """Test EventType enum."""

    def test_all_types_exist(self):
        """All event types should exist."""
        assert EventType.SAFETY_VIOLATION
        assert EventType.PFC_SOCIAL_SIGNAL
        assert EventType.TOM_BELIEF_UPDATE
        assert EventType.ESGT_IGNITION
        assert EventType.AROUSAL_CHANGE


# =============================================================================
# EVENT SEVERITY TESTS
# =============================================================================


class TestEventSeverity:
    """Test EventSeverity enum."""

    def test_all_severities_exist(self):
        """All severity levels should exist."""
        assert EventSeverity.LOW
        assert EventSeverity.MEDIUM
        assert EventSeverity.HIGH
        assert EventSeverity.CRITICAL


# =============================================================================
# CONSCIOUSNESS EVENT TESTS
# =============================================================================


class TestConsciousnessEvent:
    """Test ConsciousnessEvent data structure."""

    def test_creation(self):
        """Event should be creatable."""
        event = ConsciousnessEvent(
            event_id="evt-001",
            event_type=EventType.ESGT_IGNITION,
            severity=EventSeverity.MEDIUM,
            timestamp=1000.0,
            source="esgt",
        )
        
        assert event.event_id == "evt-001"
        assert event.event_type == EventType.ESGT_IGNITION

    def test_default_values(self):
        """Default values should be sensible."""
        event = ConsciousnessEvent(
            event_id="evt-002",
            event_type=EventType.AROUSAL_CHANGE,
            severity=EventSeverity.LOW,
            timestamp=1000.0,
            source="arousal",
        )
        
        assert event.novelty == 0.5
        assert event.processed is False


# =============================================================================
# EVENT COLLECTOR TESTS
# =============================================================================


class TestEventCollectorInit:
    """Test EventCollector initialization."""

    def test_creation(self):
        """Collector should be creatable."""
        mock_system = MagicMock()
        
        collector = EventCollector(mock_system)
        
        assert collector is not None

    def test_custom_max_events(self):
        """Custom max events should be accepted."""
        mock_system = MagicMock()
        
        collector = EventCollector(mock_system, max_events=500)
        
        assert collector.max_events == 500


class TestEventCollectorCollection:
    """Test event collection."""

    @pytest.mark.asyncio
    async def test_collect_events(self):
        """Should collect events."""
        mock_system = MagicMock()
        mock_system.esgt_coordinator = None
        mock_system.prefrontal_cortex = None
        mock_system.tom_engine = None
        mock_system.safety_protocol = None
        mock_system.arousal_controller = None
        
        collector = EventCollector(mock_system)
        
        events = await collector.collect_events()
        
        assert isinstance(events, list)

    def test_get_recent_events(self):
        """Should return recent events."""
        mock_system = MagicMock()
        collector = EventCollector(mock_system)
        
        events = collector.get_recent_events(limit=10)
        
        assert isinstance(events, list)

    def test_get_events_by_type(self):
        """Should filter events by type."""
        mock_system = MagicMock()
        collector = EventCollector(mock_system)
        
        events = collector.get_events_by_type(EventType.ESGT_IGNITION)
        
        assert isinstance(events, list)


class TestEventCollectorStats:
    """Test collection statistics."""

    def test_get_collection_stats(self):
        """Should return stats dict."""
        mock_system = MagicMock()
        collector = EventCollector(mock_system)
        
        stats = collector.get_collection_stats()
        
        assert isinstance(stats, dict)
        assert "total_events_collected" in stats


class TestEventCollectorRepr:
    """Test string representation."""

    def test_repr(self):
        """Repr should include collector info."""
        mock_system = MagicMock()
        collector = EventCollector(mock_system)
        
        repr_str = repr(collector)
        
        assert "Event" in repr_str or "Collector" in repr_str
