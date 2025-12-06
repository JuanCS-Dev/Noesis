"""Tests for esgt/enums.py and esgt/models.py"""

import time

from consciousness.esgt.enums import ESGTPhase, SalienceLevel
from consciousness.esgt.models import ESGTEvent, SalienceScore, TriggerConditions


class TestESGTPhase:
    """Test ESGTPhase enum."""

    def test_all_phases_exist(self):
        """Test all ESGT phases."""
        assert ESGTPhase.IDLE.value == "idle"
        assert ESGTPhase.PREPARE.value == "prepare"
        assert ESGTPhase.SYNCHRONIZE.value == "synchronize"
        assert ESGTPhase.BROADCAST.value == "broadcast"
        assert ESGTPhase.SUSTAIN.value == "sustain"
        assert ESGTPhase.DISSOLVE.value == "dissolve"
        assert ESGTPhase.COMPLETE.value == "complete"
        assert ESGTPhase.FAILED.value == "failed"


class TestSalienceLevel:
    """Test SalienceLevel enum."""

    def test_all_levels_exist(self):
        """Test all salience levels."""
        assert SalienceLevel.MINIMAL.value == "minimal"
        assert SalienceLevel.LOW.value == "low"
        assert SalienceLevel.MEDIUM.value == "medium"
        assert SalienceLevel.HIGH.value == "high"
        assert SalienceLevel.CRITICAL.value == "critical"


class TestSalienceScore:
    """Test SalienceScore dataclass."""

    def test_creation_defaults(self):
        """Test creating with defaults."""
        score = SalienceScore()
        
        assert score.novelty == 0.0
        assert score.relevance == 0.0
        assert score.urgency == 0.0
        assert score.confidence == 1.0
        assert score.alpha == 0.25
        assert score.beta == 0.30
        assert score.gamma == 0.30
        assert score.delta == 0.15

    def test_creation_custom(self):
        """Test creating with custom values."""
        score = SalienceScore(
            novelty=0.8,
            relevance=0.9,
            urgency=0.7,
            confidence=0.95,
            alpha=0.3,
            beta=0.3,
            gamma=0.3,
            delta=0.1,
        )
        
        assert score.novelty == 0.8
        assert score.relevance == 0.9
        assert score.urgency == 0.7
        assert score.confidence == 0.95

    def test_compute_total_default_weights(self):
        """Test computing total with default weights."""
        score = SalienceScore(
            novelty=0.8,
            relevance=0.6,
            urgency=0.4,
            confidence=0.9,
        )
        
        expected = 0.25 * 0.8 + 0.30 * 0.6 + 0.30 * 0.4 + 0.15 * 0.9
        assert abs(score.compute_total() - expected) < 0.001

    def test_compute_total_custom_weights(self):
        """Test computing total with custom weights."""
        score = SalienceScore(
            novelty=1.0,
            relevance=1.0,
            urgency=1.0,
            confidence=1.0,
            alpha=0.4,
            beta=0.3,
            gamma=0.2,
            delta=0.1,
        )
        
        expected = 0.4 * 1.0 + 0.3 * 1.0 + 0.2 * 1.0 + 0.1 * 1.0
        assert abs(score.compute_total() - expected) < 0.001

    def test_get_level_minimal(self):
        """Test minimal salience level."""
        score = SalienceScore(novelty=0.1, relevance=0.1, urgency=0.1, confidence=0.1)
        assert score.get_level() == SalienceLevel.MINIMAL

    def test_get_level_low(self):
        """Test low salience level."""
        score = SalienceScore(novelty=0.5, relevance=0.3, urgency=0.3, confidence=0.4)
        assert score.get_level() == SalienceLevel.LOW

    def test_get_level_medium(self):
        """Test medium salience level."""
        score = SalienceScore(novelty=0.7, relevance=0.6, urgency=0.6, confidence=0.7)
        assert score.get_level() == SalienceLevel.MEDIUM

    def test_get_level_high(self):
        """Test high salience level."""
        score = SalienceScore(novelty=0.8, relevance=0.8, urgency=0.8, confidence=0.8)
        assert score.get_level() == SalienceLevel.HIGH

    def test_get_level_critical(self):
        """Test critical salience level."""
        score = SalienceScore(novelty=1.0, relevance=1.0, urgency=1.0, confidence=1.0)
        assert score.get_level() == SalienceLevel.CRITICAL


class TestTriggerConditions:
    """Test TriggerConditions dataclass."""

    def test_creation_defaults(self):
        """Test creating with defaults."""
        conditions = TriggerConditions()
        
        assert conditions.min_salience == 0.60
        assert conditions.max_tig_latency_ms == 5.0
        assert conditions.min_available_nodes == 8
        assert conditions.min_cpu_capacity == 0.40
        assert conditions.refractory_period_ms == 200.0
        assert conditions.max_esgt_frequency_hz == 5.0
        assert conditions.min_arousal_level == 0.40

    def test_creation_custom(self):
        """Test creating with custom values."""
        conditions = TriggerConditions(
            min_salience=0.70,
            max_tig_latency_ms=3.0,
            min_available_nodes=10,
            min_cpu_capacity=0.50,
        )
        
        assert conditions.min_salience == 0.70
        assert conditions.max_tig_latency_ms == 3.0

    def test_check_salience_pass(self):
        """Test salience check passing."""
        conditions = TriggerConditions(min_salience=0.60)
        score = SalienceScore(novelty=0.8, relevance=0.8, urgency=0.8, confidence=0.8)
        
        assert conditions.check_salience(score) is True

    def test_check_salience_fail(self):
        """Test salience check failing."""
        conditions = TriggerConditions(min_salience=0.80)
        score = SalienceScore(novelty=0.5, relevance=0.5, urgency=0.5, confidence=0.5)
        
        assert conditions.check_salience(score) is False

    def test_check_resources_pass(self):
        """Test resource check passing."""
        conditions = TriggerConditions()
        
        assert conditions.check_resources(
            tig_latency_ms=3.0,
            available_nodes=10,
            cpu_capacity=0.50,
        ) is True

    def test_check_resources_fail_latency(self):
        """Test resource check failing on latency."""
        conditions = TriggerConditions(max_tig_latency_ms=5.0)
        
        assert conditions.check_resources(
            tig_latency_ms=10.0,  # Too high
            available_nodes=10,
            cpu_capacity=0.50,
        ) is False

    def test_check_resources_fail_nodes(self):
        """Test resource check failing on nodes."""
        conditions = TriggerConditions(min_available_nodes=8)
        
        assert conditions.check_resources(
            tig_latency_ms=3.0,
            available_nodes=5,  # Too few
            cpu_capacity=0.50,
        ) is False

    def test_check_resources_fail_cpu(self):
        """Test resource check failing on CPU."""
        conditions = TriggerConditions(min_cpu_capacity=0.40)
        
        assert conditions.check_resources(
            tig_latency_ms=3.0,
            available_nodes=10,
            cpu_capacity=0.20,  # Too low
        ) is False

    def test_check_temporal_gating_pass(self):
        """Test temporal gating passing."""
        conditions = TriggerConditions()
        
        assert conditions.check_temporal_gating(
            time_since_last_esgt=1.0,  # 1 second since last
            recent_esgt_count=2,
            time_window=1.0,
        ) is True

    def test_check_temporal_gating_fail_refractory(self):
        """Test temporal gating failing on refractory period."""
        conditions = TriggerConditions(refractory_period_ms=200.0)
        
        assert conditions.check_temporal_gating(
            time_since_last_esgt=0.1,  # 100ms - too soon
            recent_esgt_count=0,
            time_window=1.0,
        ) is False

    def test_check_temporal_gating_fail_frequency(self):
        """Test temporal gating failing on frequency limit."""
        conditions = TriggerConditions(max_esgt_frequency_hz=5.0)
        
        assert conditions.check_temporal_gating(
            time_since_last_esgt=1.0,
            recent_esgt_count=10,  # 10 events in 1 second = 10 Hz
            time_window=1.0,
        ) is False

    def test_check_arousal_pass(self):
        """Test arousal check passing."""
        conditions = TriggerConditions(min_arousal_level=0.40)
        
        assert conditions.check_arousal(0.50) is True

    def test_check_arousal_fail(self):
        """Test arousal check failing."""
        conditions = TriggerConditions(min_arousal_level=0.60)
        
        assert conditions.check_arousal(0.30) is False


class TestESGTEvent:
    """Test ESGTEvent dataclass."""

    def test_creation_minimal(self):
        """Test creating event with minimal fields."""
        event = ESGTEvent(
            event_id="evt-001",
            timestamp_start=time.time(),
        )
        
        assert event.event_id == "evt-001"
        assert event.timestamp_end is None
        assert event.content == {}
        assert event.content_source == ""
        assert event.participating_nodes == set()
        assert event.node_count == 0
        assert event.current_phase == ESGTPhase.IDLE
        assert event.success is False

    def test_creation_complete(self):
        """Test creating event with all fields."""
        nodes = {"node1", "node2", "node3"}
        event = ESGTEvent(
            event_id="evt-002",
            timestamp_start=1234567890.0,
            timestamp_end=1234567891.0,
            content={"data": "test"},
            content_source="SPM-visual",
            participating_nodes=nodes,
            node_count=3,
            target_coherence=0.80,
            achieved_coherence=0.75,
            current_phase=ESGTPhase.BROADCAST,
            success=True,
        )
        
        assert event.event_id == "evt-002"
        assert event.content == {"data": "test"}
        assert event.participating_nodes == nodes
        assert event.target_coherence == 0.80
        assert event.success is True

    def test_transition_phase(self):
        """Test phase transition."""
        event = ESGTEvent(event_id="evt-003", timestamp_start=time.time())
        
        assert event.current_phase == ESGTPhase.IDLE
        assert len(event.phase_transitions) == 0
        
        event.transition_phase(ESGTPhase.PREPARE)
        
        assert event.current_phase == ESGTPhase.PREPARE
        assert len(event.phase_transitions) == 1
        assert event.phase_transitions[0][0] == ESGTPhase.PREPARE

    def test_transition_phase_multiple(self):
        """Test multiple phase transitions."""
        event = ESGTEvent(event_id="evt-004", timestamp_start=time.time())
        
        event.transition_phase(ESGTPhase.PREPARE)
        event.transition_phase(ESGTPhase.SYNCHRONIZE)
        event.transition_phase(ESGTPhase.BROADCAST)
        
        assert event.current_phase == ESGTPhase.BROADCAST
        assert len(event.phase_transitions) == 3
        assert event.phase_transitions[2][0] == ESGTPhase.BROADCAST

    def test_finalize_success(self):
        """Test finalizing successful event."""
        start = time.time()
        event = ESGTEvent(event_id="evt-005", timestamp_start=start)
        
        time.sleep(0.01)  # Small delay
        event.finalize(success=True)
        
        assert event.success is True
        assert event.failure_reason is None
        assert event.timestamp_end is not None
        assert event.total_duration_ms > 0

    def test_finalize_failure(self):
        """Test finalizing failed event."""
        event = ESGTEvent(event_id="evt-006", timestamp_start=time.time())
        
        event.finalize(success=False, reason="Coherence not achieved")
        
        assert event.success is False
        assert event.failure_reason == "Coherence not achieved"
        assert event.timestamp_end is not None

    def test_get_duration_ms_completed(self):
        """Test getting duration for completed event."""
        event = ESGTEvent(
            event_id="evt-007",
            timestamp_start=1000.0,
            timestamp_end=1000.5,
        )
        
        duration = event.get_duration_ms()
        assert abs(duration - 500.0) < 0.1  # 500ms

    def test_get_duration_ms_ongoing(self):
        """Test getting duration for ongoing event."""
        start = time.time()
        event = ESGTEvent(event_id="evt-008", timestamp_start=start)
        
        time.sleep(0.01)
        duration = event.get_duration_ms()
        
        assert duration > 0

    def test_was_successful_true(self):
        """Test successful event with good coherence."""
        event = ESGTEvent(
            event_id="evt-009",
            timestamp_start=time.time(),
            target_coherence=0.70,
            achieved_coherence=0.75,
            success=True,
        )
        
        assert event.was_successful() is True

    def test_was_successful_false_not_successful(self):
        """Test unsuccessful event."""
        event = ESGTEvent(
            event_id="evt-010",
            timestamp_start=time.time(),
            target_coherence=0.70,
            achieved_coherence=0.75,
            success=False,  # Not successful
        )
        
        assert event.was_successful() is False

    def test_was_successful_false_low_coherence(self):
        """Test successful event but low coherence."""
        event = ESGTEvent(
            event_id="evt-011",
            timestamp_start=time.time(),
            target_coherence=0.70,
            achieved_coherence=0.50,  # Below target
            success=True,
        )
        
        assert event.was_successful() is False

    def test_coherence_history(self):
        """Test coherence history tracking."""
        event = ESGTEvent(event_id="evt-012", timestamp_start=time.time())
        
        assert event.coherence_history == []
        
        event.coherence_history.append(0.30)
        event.coherence_history.append(0.50)
        event.coherence_history.append(0.70)
        
        assert len(event.coherence_history) == 3
        assert event.coherence_history[-1] == 0.70
