"""
Comprehensive tests for MCEA models (models.py, stress_models.py)

Tests cover:
- ArousalLevel enum
- ArousalState dataclass
- ArousalModulation dataclass
- ArousalConfig dataclass
- StressLevel enum
- StressType enum
- StressResponse dataclass
- StressTestConfig dataclass
"""

import time

import pytest

from consciousness.mcea.models import (
    ArousalConfig,
    ArousalLevel,
    ArousalModulation,
    ArousalState,
)
from consciousness.mcea.stress_models import (
    StressLevel,
    StressResponse,
    StressTestConfig,
    StressType,
)


# ==================== AROUSAL MODELS TESTS ====================


class TestArousalLevel:
    """Test ArousalLevel enum."""

    def test_all_arousal_levels_exist(self):
        """Test that all expected arousal levels are defined."""
        assert ArousalLevel.SLEEP.value == "sleep"
        assert ArousalLevel.DROWSY.value == "drowsy"
        assert ArousalLevel.RELAXED.value == "relaxed"
        assert ArousalLevel.ALERT.value == "alert"
        assert ArousalLevel.HYPERALERT.value == "hyperalert"

    def test_arousal_level_count(self):
        """Test that we have all expected arousal levels."""
        assert len(ArousalLevel) == 5


class TestArousalState:
    """Test ArousalState dataclass."""

    def test_creation_minimal(self):
        """Test creating arousal state with minimal fields."""
        state = ArousalState()

        assert state.arousal == 0.6
        assert state.level == ArousalLevel.RELAXED
        assert state.baseline_arousal == 0.6
        assert state.esgt_salience_threshold == 0.70

    def test_auto_classification_sleep(self):
        """Test automatic classification for SLEEP level."""
        state = ArousalState(arousal=0.1)
        assert state.level == ArousalLevel.SLEEP

        state = ArousalState(arousal=0.2)
        assert state.level == ArousalLevel.SLEEP

    def test_auto_classification_drowsy(self):
        """Test automatic classification for DROWSY level."""
        state = ArousalState(arousal=0.3)
        assert state.level == ArousalLevel.DROWSY

        state = ArousalState(arousal=0.4)
        assert state.level == ArousalLevel.DROWSY

    def test_auto_classification_relaxed(self):
        """Test automatic classification for RELAXED level."""
        state = ArousalState(arousal=0.5)
        assert state.level == ArousalLevel.RELAXED

        state = ArousalState(arousal=0.6)
        assert state.level == ArousalLevel.RELAXED

    def test_auto_classification_alert(self):
        """Test automatic classification for ALERT level."""
        state = ArousalState(arousal=0.7)
        assert state.level == ArousalLevel.ALERT

        state = ArousalState(arousal=0.8)
        assert state.level == ArousalLevel.ALERT

    def test_auto_classification_hyperalert(self):
        """Test automatic classification for HYPERALERT level."""
        state = ArousalState(arousal=0.9)
        assert state.level == ArousalLevel.HYPERALERT

        state = ArousalState(arousal=1.0)
        assert state.level == ArousalLevel.HYPERALERT

    def test_get_arousal_factor(self):
        """Test arousal factor computation."""
        # Low arousal should give small factor
        state_low = ArousalState(arousal=0.0)
        assert state_low.get_arousal_factor() == 0.5

        # High arousal should give large factor
        state_high = ArousalState(arousal=1.0)
        assert state_high.get_arousal_factor() == 2.0

        # Medium arousal
        state_mid = ArousalState(arousal=0.6)
        assert abs(state_mid.get_arousal_factor() - 1.4) < 0.01

    def test_compute_effective_threshold(self):
        """Test effective threshold computation."""
        # Low arousal -> higher threshold (harder to trigger)
        state_low = ArousalState(arousal=0.0)
        threshold_low = state_low.compute_effective_threshold(0.70)
        assert threshold_low > 0.70

        # High arousal -> lower threshold (easier to trigger)
        state_high = ArousalState(arousal=1.0)
        threshold_high = state_high.compute_effective_threshold(0.70)
        assert threshold_high < 0.70

        # Medium arousal ~= base threshold
        state_mid = ArousalState(arousal=0.6)
        threshold_mid = state_mid.compute_effective_threshold(0.70)
        assert abs(threshold_mid - 0.5) < 0.1

    def test_creation_complete(self):
        """Test creating arousal state with all fields."""
        state = ArousalState(
            arousal=0.8,
            baseline_arousal=0.6,
            need_contribution=0.1,
            external_contribution=0.1,
            temporal_contribution=0.05,
            circadian_contribution=0.05,
            esgt_salience_threshold=0.65,
            time_in_current_level_seconds=10.0,
        )

        assert state.arousal == 0.8
        assert state.level == ArousalLevel.ALERT
        assert state.need_contribution == 0.1
        assert state.time_in_current_level_seconds == 10.0

    def test_repr(self):
        """Test string representation."""
        state = ArousalState(arousal=0.75)
        repr_str = repr(state)

        assert "0.75" in repr_str
        assert "alert" in repr_str
        assert "threshold" in repr_str


class TestArousalModulation:
    """Test ArousalModulation dataclass."""

    def test_creation_minimal(self):
        """Test creating arousal modulation with minimal fields."""
        mod = ArousalModulation(source="test", delta=0.1)

        assert mod.source == "test"
        assert mod.delta == 0.1
        assert mod.duration_seconds == 0.0
        assert mod.priority == 1

    def test_instant_modulation_expired(self):
        """Test that instant modulation (duration=0) is always expired."""
        mod = ArousalModulation(source="test", delta=0.1, duration_seconds=0.0)
        assert mod.is_expired() is True

    def test_duration_modulation_not_expired(self):
        """Test that duration-based modulation is not expired initially."""
        mod = ArousalModulation(source="test", delta=0.1, duration_seconds=10.0)
        assert mod.is_expired() is False

    def test_duration_modulation_expires(self):
        """Test that duration-based modulation expires after time."""
        mod = ArousalModulation(
            source="test", delta=0.1, duration_seconds=0.1  # 100ms
        )
        time.sleep(0.15)  # Wait 150ms
        assert mod.is_expired() is True

    def test_get_current_delta_instant(self):
        """Test current delta for instant modulation."""
        mod = ArousalModulation(source="test", delta=0.5, duration_seconds=0.0)
        assert mod.get_current_delta() == 0.5

    def test_get_current_delta_duration_full(self):
        """Test current delta at start of duration."""
        mod = ArousalModulation(source="test", delta=0.4, duration_seconds=10.0)
        # At start, should get full delta
        assert abs(mod.get_current_delta() - 0.4) < 0.05

    def test_get_current_delta_duration_expired(self):
        """Test current delta after duration expires."""
        mod = ArousalModulation(
            source="test", delta=0.4, duration_seconds=0.05  # 50ms
        )
        time.sleep(0.1)  # Wait 100ms
        assert mod.get_current_delta() == 0.0

    def test_get_current_delta_duration_decay(self):
        """Test that delta decays over time."""
        mod = ArousalModulation(source="test", delta=0.4, duration_seconds=1.0)
        initial_delta = mod.get_current_delta()

        time.sleep(0.5)  # Wait half the duration
        mid_delta = mod.get_current_delta()

        # Delta should have decayed
        assert mid_delta < initial_delta
        assert mid_delta > 0.0

    def test_priority(self):
        """Test priority field."""
        low_priority = ArousalModulation(source="test1", delta=0.1, priority=1)
        high_priority = ArousalModulation(source="test2", delta=0.1, priority=10)

        assert low_priority.priority == 1
        assert high_priority.priority == 10


class TestArousalConfig:
    """Test ArousalConfig dataclass."""

    def test_default_values(self):
        """Test that default configuration values are sensible."""
        config = ArousalConfig()

        assert config.baseline_arousal == 0.6
        assert config.update_interval_ms == 100.0
        assert config.arousal_increase_rate == 0.05
        assert config.arousal_decrease_rate == 0.02
        assert config.min_arousal == 0.0
        assert config.max_arousal == 1.0

    def test_need_weights(self):
        """Test need influence weights."""
        config = ArousalConfig()

        assert config.repair_need_weight == 0.3
        assert config.rest_need_weight == -0.2  # Negative: rest lowers arousal
        assert config.efficiency_need_weight == 0.1
        assert config.connectivity_need_weight == 0.15

    def test_stress_parameters(self):
        """Test stress buildup parameters."""
        config = ArousalConfig()

        assert config.stress_buildup_rate == 0.01
        assert config.stress_recovery_rate == 0.005
        assert config.stress_recovery_rate < config.stress_buildup_rate

    def test_esgt_refractory_parameters(self):
        """Test ESGT refractory parameters."""
        config = ArousalConfig()

        assert config.esgt_refractory_arousal_drop == 0.1
        assert config.esgt_refractory_duration_seconds == 5.0

    def test_circadian_disabled_by_default(self):
        """Test that circadian rhythm is disabled by default."""
        config = ArousalConfig()
        assert config.enable_circadian is False

    def test_custom_configuration(self):
        """Test creating custom configuration."""
        config = ArousalConfig(
            baseline_arousal=0.5,
            update_interval_ms=50.0,
            arousal_increase_rate=0.1,
            enable_circadian=True,
            circadian_amplitude=0.15,
        )

        assert config.baseline_arousal == 0.5
        assert config.update_interval_ms == 50.0
        assert config.arousal_increase_rate == 0.1
        assert config.enable_circadian is True
        assert config.circadian_amplitude == 0.15


# ==================== STRESS MODELS TESTS ====================


class TestStressLevel:
    """Test StressLevel enum."""

    def test_all_stress_levels_exist(self):
        """Test that all expected stress levels are defined."""
        assert StressLevel.NONE.value == "none"
        assert StressLevel.MILD.value == "mild"
        assert StressLevel.MODERATE.value == "moderate"
        assert StressLevel.SEVERE.value == "severe"
        assert StressLevel.CRITICAL.value == "critical"

    def test_stress_level_count(self):
        """Test that we have all expected stress levels."""
        assert len(StressLevel) == 5


class TestStressType:
    """Test StressType enum."""

    def test_all_stress_types_exist(self):
        """Test that all expected stress types are defined."""
        assert StressType.COMPUTATIONAL_LOAD.value == "computational_load"
        assert StressType.ERROR_INJECTION.value == "error_injection"
        assert StressType.NETWORK_DEGRADATION.value == "network_degradation"
        assert StressType.AROUSAL_FORCING.value == "arousal_forcing"
        assert StressType.RAPID_CHANGE.value == "rapid_change"
        assert StressType.COMBINED.value == "combined"

    def test_stress_type_count(self):
        """Test that we have all expected stress types."""
        assert len(StressType) == 6


class TestStressResponse:
    """Test StressResponse dataclass."""

    def test_creation_healthy_response(self):
        """Test creating stress response for healthy system."""
        response = StressResponse(
            stress_type=StressType.COMPUTATIONAL_LOAD,
            stress_level=StressLevel.MODERATE,
            initial_arousal=0.6,
            peak_arousal=0.75,
            final_arousal=0.65,
            arousal_stability_cv=0.15,
            peak_rest_need=0.4,
            peak_repair_need=0.3,
            peak_efficiency_need=0.2,
            goals_generated=5,
            goals_satisfied=4,
            critical_goals_generated=1,
            esgt_events=10,
            mean_esgt_coherence=0.85,
            esgt_coherence_degradation=0.05,
            recovery_time_seconds=30.0,
            full_recovery_achieved=True,
            arousal_runaway_detected=False,
            goal_generation_failure=False,
            coherence_collapse=False,
            duration_seconds=45.0,
        )

        assert response.passed_stress_test() is True
        assert response.get_resilience_score() > 80.0

    def test_creation_failed_response(self):
        """Test creating stress response for failed system."""
        response = StressResponse(
            stress_type=StressType.AROUSAL_FORCING,
            stress_level=StressLevel.CRITICAL,
            initial_arousal=0.6,
            peak_arousal=0.98,
            final_arousal=0.95,
            arousal_stability_cv=0.45,
            peak_rest_need=0.9,
            peak_repair_need=0.8,
            peak_efficiency_need=0.7,
            goals_generated=20,
            goals_satisfied=2,
            critical_goals_generated=15,
            esgt_events=50,
            mean_esgt_coherence=0.35,
            esgt_coherence_degradation=0.40,
            recovery_time_seconds=150.0,
            full_recovery_achieved=False,
            arousal_runaway_detected=True,
            goal_generation_failure=True,
            coherence_collapse=True,
            duration_seconds=60.0,
        )

        assert response.passed_stress_test() is False
        assert response.get_resilience_score() < 20.0

    def test_resilience_score_arousal_runaway(self):
        """Test resilience score with arousal runaway."""
        response = StressResponse(
            stress_type=StressType.COMPUTATIONAL_LOAD,
            stress_level=StressLevel.SEVERE,
            initial_arousal=0.6,
            peak_arousal=0.95,
            final_arousal=0.7,
            arousal_stability_cv=0.2,
            peak_rest_need=0.5,
            peak_repair_need=0.4,
            peak_efficiency_need=0.3,
            goals_generated=5,
            goals_satisfied=4,
            critical_goals_generated=1,
            esgt_events=10,
            mean_esgt_coherence=0.80,
            esgt_coherence_degradation=0.10,
            recovery_time_seconds=40.0,
            full_recovery_achieved=True,
            arousal_runaway_detected=True,  # Only failure
            goal_generation_failure=False,
            coherence_collapse=False,
            duration_seconds=50.0,
        )

        score = response.get_resilience_score()
        assert score == 60.0  # 100 - 40 (arousal runaway)

    def test_resilience_score_goal_failure(self):
        """Test resilience score with goal generation failure."""
        response = StressResponse(
            stress_type=StressType.ERROR_INJECTION,
            stress_level=StressLevel.MODERATE,
            initial_arousal=0.6,
            peak_arousal=0.7,
            final_arousal=0.65,
            arousal_stability_cv=0.15,
            peak_rest_need=0.3,
            peak_repair_need=0.3,
            peak_efficiency_need=0.2,
            goals_generated=0,
            goals_satisfied=0,
            critical_goals_generated=0,
            esgt_events=10,
            mean_esgt_coherence=0.85,
            esgt_coherence_degradation=0.05,
            recovery_time_seconds=30.0,
            full_recovery_achieved=True,
            arousal_runaway_detected=False,
            goal_generation_failure=True,  # Only failure
            coherence_collapse=False,
            duration_seconds=45.0,
        )

        score = response.get_resilience_score()
        assert score == 80.0  # 100 - 20 (goal failure)

    def test_resilience_score_coherence_collapse(self):
        """Test resilience score with coherence collapse."""
        response = StressResponse(
            stress_type=StressType.RAPID_CHANGE,
            stress_level=StressLevel.SEVERE,
            initial_arousal=0.6,
            peak_arousal=0.75,
            final_arousal=0.65,
            arousal_stability_cv=0.15,
            peak_rest_need=0.4,
            peak_repair_need=0.3,
            peak_efficiency_need=0.2,
            goals_generated=5,
            goals_satisfied=4,
            critical_goals_generated=1,
            esgt_events=10,
            mean_esgt_coherence=0.40,
            esgt_coherence_degradation=0.45,
            recovery_time_seconds=30.0,
            full_recovery_achieved=True,
            arousal_runaway_detected=False,
            goal_generation_failure=False,
            coherence_collapse=True,  # Only failure
            duration_seconds=45.0,
        )

        score = response.get_resilience_score()
        assert score == 70.0  # 100 - 30 (coherence collapse)

    def test_resilience_score_slow_recovery(self):
        """Test resilience score with slow but successful recovery."""
        response = StressResponse(
            stress_type=StressType.COMPUTATIONAL_LOAD,
            stress_level=StressLevel.MODERATE,
            initial_arousal=0.6,
            peak_arousal=0.7,
            final_arousal=0.65,
            arousal_stability_cv=0.15,
            peak_rest_need=0.3,
            peak_repair_need=0.3,
            peak_efficiency_need=0.2,
            goals_generated=5,
            goals_satisfied=4,
            critical_goals_generated=1,
            esgt_events=10,
            mean_esgt_coherence=0.85,
            esgt_coherence_degradation=0.05,
            recovery_time_seconds=80.0,  # Slow recovery (> 60s)
            full_recovery_achieved=True,
            arousal_runaway_detected=False,
            goal_generation_failure=False,
            coherence_collapse=False,
            duration_seconds=100.0,
        )

        score = response.get_resilience_score()
        assert score == 90.0  # 100 - 10 (slow recovery)

    def test_resilience_score_no_recovery(self):
        """Test resilience score without recovery."""
        response = StressResponse(
            stress_type=StressType.COMBINED,
            stress_level=StressLevel.CRITICAL,
            initial_arousal=0.6,
            peak_arousal=0.9,
            final_arousal=0.85,
            arousal_stability_cv=0.25,
            peak_rest_need=0.7,
            peak_repair_need=0.6,
            peak_efficiency_need=0.5,
            goals_generated=10,
            goals_satisfied=3,
            critical_goals_generated=5,
            esgt_events=20,
            mean_esgt_coherence=0.70,
            esgt_coherence_degradation=0.15,
            recovery_time_seconds=50.0,
            full_recovery_achieved=False,  # No recovery
            arousal_runaway_detected=False,
            goal_generation_failure=False,
            coherence_collapse=False,
            duration_seconds=70.0,
        )

        score = response.get_resilience_score()
        assert score == 85.0  # 100 - 15 (no full recovery)

    def test_resilience_score_high_arousal_instability(self):
        """Test resilience score with high arousal instability."""
        response = StressResponse(
            stress_type=StressType.NETWORK_DEGRADATION,
            stress_level=StressLevel.MODERATE,
            initial_arousal=0.6,
            peak_arousal=0.7,
            final_arousal=0.65,
            arousal_stability_cv=0.35,  # High instability (> 0.3)
            peak_rest_need=0.3,
            peak_repair_need=0.3,
            peak_efficiency_need=0.2,
            goals_generated=5,
            goals_satisfied=4,
            critical_goals_generated=1,
            esgt_events=10,
            mean_esgt_coherence=0.85,
            esgt_coherence_degradation=0.05,
            recovery_time_seconds=30.0,
            full_recovery_achieved=True,
            arousal_runaway_detected=False,
            goal_generation_failure=False,
            coherence_collapse=False,
            duration_seconds=45.0,
        )

        score = response.get_resilience_score()
        assert score == 90.0  # 100 - 10 (high arousal instability)

    def test_resilience_score_minimum_zero(self):
        """Test that resilience score never goes below zero."""
        response = StressResponse(
            stress_type=StressType.COMBINED,
            stress_level=StressLevel.CRITICAL,
            initial_arousal=0.6,
            peak_arousal=0.98,
            final_arousal=0.95,
            arousal_stability_cv=0.50,
            peak_rest_need=0.9,
            peak_repair_need=0.9,
            peak_efficiency_need=0.8,
            goals_generated=20,
            goals_satisfied=1,
            critical_goals_generated=18,
            esgt_events=50,
            mean_esgt_coherence=0.30,
            esgt_coherence_degradation=0.50,
            recovery_time_seconds=200.0,
            full_recovery_achieved=False,
            arousal_runaway_detected=True,
            goal_generation_failure=True,
            coherence_collapse=True,
            duration_seconds=250.0,
        )

        score = response.get_resilience_score()
        assert score == 0.0  # Can't go below 0

    def test_passed_stress_test_all_criteria(self):
        """Test stress test pass criteria."""
        # Passing response
        pass_response = StressResponse(
            stress_type=StressType.COMPUTATIONAL_LOAD,
            stress_level=StressLevel.MODERATE,
            initial_arousal=0.6,
            peak_arousal=0.7,
            final_arousal=0.65,
            arousal_stability_cv=0.15,
            peak_rest_need=0.3,
            peak_repair_need=0.3,
            peak_efficiency_need=0.2,
            goals_generated=5,
            goals_satisfied=4,
            critical_goals_generated=1,
            esgt_events=10,
            mean_esgt_coherence=0.85,
            esgt_coherence_degradation=0.05,
            recovery_time_seconds=60.0,
            full_recovery_achieved=True,
            arousal_runaway_detected=False,
            goal_generation_failure=False,
            coherence_collapse=False,
            duration_seconds=80.0,
        )

        assert pass_response.passed_stress_test() is True

    def test_passed_stress_test_slow_recovery_fails(self):
        """Test that slow recovery (>120s) fails the stress test."""
        slow_response = StressResponse(
            stress_type=StressType.COMPUTATIONAL_LOAD,
            stress_level=StressLevel.MODERATE,
            initial_arousal=0.6,
            peak_arousal=0.7,
            final_arousal=0.65,
            arousal_stability_cv=0.15,
            peak_rest_need=0.3,
            peak_repair_need=0.3,
            peak_efficiency_need=0.2,
            goals_generated=5,
            goals_satisfied=4,
            critical_goals_generated=1,
            esgt_events=10,
            mean_esgt_coherence=0.85,
            esgt_coherence_degradation=0.05,
            recovery_time_seconds=130.0,  # Too slow
            full_recovery_achieved=True,
            arousal_runaway_detected=False,
            goal_generation_failure=False,
            coherence_collapse=False,
            duration_seconds=150.0,
        )

        assert slow_response.passed_stress_test() is False

    def test_repr(self):
        """Test string representation."""
        response = StressResponse(
            stress_type=StressType.COMPUTATIONAL_LOAD,
            stress_level=StressLevel.MODERATE,
            initial_arousal=0.6,
            peak_arousal=0.7,
            final_arousal=0.65,
            arousal_stability_cv=0.15,
            peak_rest_need=0.3,
            peak_repair_need=0.3,
            peak_efficiency_need=0.2,
            goals_generated=5,
            goals_satisfied=4,
            critical_goals_generated=1,
            esgt_events=10,
            mean_esgt_coherence=0.85,
            esgt_coherence_degradation=0.05,
            recovery_time_seconds=30.0,
            full_recovery_achieved=True,
            arousal_runaway_detected=False,
            goal_generation_failure=False,
            coherence_collapse=False,
            duration_seconds=45.0,
        )

        repr_str = repr(response)
        assert "computational_load" in repr_str
        assert "moderate" in repr_str
        assert "PASS" in repr_str or "resilience" in repr_str


class TestStressTestConfig:
    """Test StressTestConfig dataclass."""

    def test_default_values(self):
        """Test default stress test configuration."""
        config = StressTestConfig()

        assert config.stress_duration_seconds == 30.0
        assert config.recovery_duration_seconds == 60.0
        assert config.arousal_runaway_threshold == 0.95
        assert config.arousal_runaway_duration == 10.0
        assert config.coherence_collapse_threshold == 0.50
        assert config.recovery_baseline_tolerance == 0.1

    def test_stress_parameters(self):
        """Test stress simulation parameters."""
        config = StressTestConfig()

        assert config.load_stress_cpu_percent == 90.0
        assert config.error_stress_rate_per_min == 20.0
        assert config.network_stress_latency_ms == 200.0
        assert config.arousal_forcing_target == 0.9

    def test_custom_configuration(self):
        """Test creating custom stress test configuration."""
        config = StressTestConfig(
            stress_duration_seconds=60.0,
            recovery_duration_seconds=120.0,
            arousal_runaway_threshold=0.90,
            coherence_collapse_threshold=0.40,
            load_stress_cpu_percent=95.0,
        )

        assert config.stress_duration_seconds == 60.0
        assert config.recovery_duration_seconds == 120.0
        assert config.arousal_runaway_threshold == 0.90
        assert config.coherence_collapse_threshold == 0.40
        assert config.load_stress_cpu_percent == 95.0
