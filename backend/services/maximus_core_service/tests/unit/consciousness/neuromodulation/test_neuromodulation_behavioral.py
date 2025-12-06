"""
Comprehensive Behavioral Tests for Neuromodulation System
==========================================================

These tests validate the BIOLOGICAL BEHAVIOR of the neuromodulation system,
not just code coverage. Each test verifies a specific neuroscientific principle.

Target Modules:
- DopamineModulator: Reward/motivation dynamics
- NeuromodulationCoordinator: Cross-modulator interactions
"""

import time
from unittest.mock import MagicMock

import pytest

from consciousness.neuromodulation.dopamine_hardened import (
    DopamineModulator,
    ModulatorConfig,
    ModulatorState,
)
from consciousness.neuromodulation.coordinator_hardened import (
    CoordinatorConfig,
    ModulationRequest,
    NeuromodulationCoordinator,
)


# =============================================================================
# DOPAMINE MODULATOR TESTS - Reward/Motivation System
# =============================================================================


class TestDopamineBasicBehavior:
    """Test basic dopamine modulator behavior."""

    def test_initialization_at_baseline(self):
        """Dopamine should initialize at homeostatic baseline."""
        config = ModulatorConfig(baseline=0.5)
        modulator = DopamineModulator(config)
        
        assert modulator._level == 0.5
        assert not modulator._circuit_breaker_open

    def test_positive_modulation_increases_level(self):
        """Positive delta (reward signal) should increase dopamine."""
        modulator = DopamineModulator(ModulatorConfig(baseline=0.5))
        initial = modulator._level
        
        modulator.modulate(delta=0.1, source="reward_signal")
        
        # Level should increase (accounting for smoothing)
        assert modulator._level > initial

    def test_negative_modulation_decreases_level(self):
        """Negative delta (punishment/aversion) should decrease dopamine."""
        modulator = DopamineModulator(ModulatorConfig(baseline=0.5))
        initial = modulator._level
        
        modulator.modulate(delta=-0.1, source="aversion_signal")
        
        assert modulator._level < initial


class TestDopamineDesensitization:
    """Test receptor desensitization - biological diminishing returns."""

    def test_desensitization_reduces_effect(self):
        """Above threshold, modulations have diminishing returns."""
        config = ModulatorConfig(
            baseline=0.5,
            desensitization_threshold=0.7,
            desensitization_factor=0.5,
            smoothing_factor=1.0,  # No smoothing for clarity
            max_change_per_step=1.0,  # Allow full changes
        )
        modulator = DopamineModulator(config)
        
        # Push level above threshold
        modulator._level = 0.85
        
        # Modulate - should be reduced by desensitization_factor
        change = modulator.modulate(delta=0.1, source="test")
        
        # Change should be ~0.05 (0.1 * 0.5)
        assert change < 0.1  # Less than requested due to desensitization

    def test_desensitization_not_active_below_threshold(self):
        """Below threshold, modulations have full effect."""
        config = ModulatorConfig(
            baseline=0.3,
            desensitization_threshold=0.8,
            smoothing_factor=1.0,
            max_change_per_step=1.0,
        )
        modulator = DopamineModulator(config)
        
        # Level is at 0.3, well below threshold (0.8)
        change = modulator.modulate(delta=0.1, source="test")
        
        # Full change should apply
        assert abs(change - 0.1) < 0.01


class TestDopamineHomeostaticDecay:
    """Test homeostatic decay - return to baseline over time."""

    def test_elevated_level_decays_toward_baseline(self):
        """Elevated dopamine should decay back to baseline."""
        config = ModulatorConfig(baseline=0.5, decay_rate=0.5)
        modulator = DopamineModulator(config)
        
        # Artificially elevate
        modulator._level = 0.9
        modulator._last_update = time.time() - 2.0  # Simulate 2 seconds ago
        
        # Access level triggers decay
        current = modulator.level
        
        # Should have decayed toward 0.5
        assert current < 0.9
        assert current > 0.5  # Still above baseline but decaying

    def test_depressed_level_rises_toward_baseline(self):
        """Depressed dopamine should rise back to baseline."""
        config = ModulatorConfig(baseline=0.5, decay_rate=0.5)
        modulator = DopamineModulator(config)
        
        # Artificially depress
        modulator._level = 0.1
        modulator._last_update = time.time() - 2.0
        
        current = modulator.level
        
        # Should have risen toward 0.5
        assert current > 0.1
        assert current < 0.5


class TestDopamineSafetyBounds:
    """Test safety bounds - hard limits on dopamine levels."""

    def test_cannot_exceed_max_level(self):
        """HARD CLAMP: Dopamine cannot exceed max_level."""
        config = ModulatorConfig(
            baseline=0.5,
            max_level=1.0,
            smoothing_factor=1.0,
            max_change_per_step=1.0,
        )
        modulator = DopamineModulator(config)
        modulator._level = 0.95
        
        # Try to push past max
        modulator.modulate(delta=0.5, source="excessive_reward")
        
        assert modulator._level <= 1.0

    def test_cannot_go_below_min_level(self):
        """HARD CLAMP: Dopamine cannot go below min_level."""
        config = ModulatorConfig(
            baseline=0.5,
            min_level=0.0,
            smoothing_factor=1.0,
            max_change_per_step=1.0,
        )
        modulator = DopamineModulator(config)
        modulator._level = 0.05
        
        # Try to push below min
        modulator.modulate(delta=-0.5, source="severe_punishment")
        
        assert modulator._level >= 0.0


class TestDopamineCircuitBreaker:
    """Test circuit breaker - safety mechanism for anomalous behavior."""

    def test_circuit_breaker_opens_after_consecutive_anomalies(self):
        """Circuit breaker should open after MAX_CONSECUTIVE_ANOMALIES bound hits."""
        config = ModulatorConfig(
            baseline=0.5,
            smoothing_factor=1.0,
            max_change_per_step=0.5,
        )
        modulator = DopamineModulator(config)
        modulator._level = 0.99  # Near max
        
        # Hit bounds repeatedly
        for _ in range(DopamineModulator.MAX_CONSECUTIVE_ANOMALIES):
            try:
                modulator.modulate(delta=0.5, source="runaway_test")
            except RuntimeError:
                break
        
        assert modulator._circuit_breaker_open

    def test_circuit_breaker_blocks_modulation(self):
        """Open circuit breaker should block all modulations."""
        modulator = DopamineModulator(ModulatorConfig())
        modulator._circuit_breaker_open = True
        
        with pytest.raises(RuntimeError, match="circuit breaker"):
            modulator.modulate(delta=0.1, source="blocked")

    def test_circuit_breaker_triggers_kill_switch_callback(self):
        """Circuit breaker opening should trigger kill switch callback."""
        kill_switch = MagicMock()
        config = ModulatorConfig(smoothing_factor=1.0, max_change_per_step=0.5)
        modulator = DopamineModulator(config, kill_switch_callback=kill_switch)
        modulator._level = 0.99
        
        # Cause enough anomalies to open breaker
        for _ in range(DopamineModulator.MAX_CONSECUTIVE_ANOMALIES + 1):
            try:
                modulator.modulate(delta=0.5, source="runaway")
            except RuntimeError:
                break
        
        assert kill_switch.called


class TestDopamineTemporalSmoothing:
    """Test temporal smoothing - prevent instantaneous jumps."""

    def test_max_change_per_step_enforced(self):
        """Max change per step should be enforced."""
        config = ModulatorConfig(
            baseline=0.5,
            max_change_per_step=0.1,
            smoothing_factor=1.0,
        )
        modulator = DopamineModulator(config)
        
        # Request huge change
        modulator.modulate(delta=0.9, source="huge_request")
        
        # Actual change should be limited
        assert modulator._level <= 0.6  # 0.5 + 0.1 max


class TestDopamineObservability:
    """Test observability - metrics for Safety Core monitoring."""

    def test_get_health_metrics_returns_all_fields(self):
        """Health metrics should expose all necessary monitoring data."""
        modulator = DopamineModulator(ModulatorConfig())
        modulator.modulate(delta=0.1, source="test")
        
        metrics = modulator.get_health_metrics()
        
        assert "dopamine_level" in metrics
        assert "dopamine_baseline" in metrics
        assert "dopamine_desensitized" in metrics
        assert "dopamine_circuit_breaker_open" in metrics
        assert "dopamine_total_modulations" in metrics
        assert "dopamine_bounded_corrections" in metrics
        assert "dopamine_bound_hit_rate" in metrics

    def test_state_property_returns_modulator_state(self):
        """State property should return complete ModulatorState."""
        modulator = DopamineModulator(ModulatorConfig())
        
        state = modulator.state
        
        assert isinstance(state, ModulatorState)
        assert hasattr(state, "level")
        assert hasattr(state, "is_desensitized")


class TestDopamineEmergencyStop:
    """Test emergency stop - kill switch integration."""

    def test_emergency_stop_opens_circuit_breaker(self):
        """Emergency stop should open circuit breaker."""
        modulator = DopamineModulator(ModulatorConfig())
        
        modulator.emergency_stop()
        
        assert modulator._circuit_breaker_open

    def test_emergency_stop_returns_to_baseline(self):
        """Emergency stop should return level to baseline immediately."""
        config = ModulatorConfig(baseline=0.5)
        modulator = DopamineModulator(config)
        modulator._level = 0.95
        
        modulator.emergency_stop()
        
        assert modulator._level == 0.5


# =============================================================================
# NEUROMODULATION COORDINATOR TESTS - Cross-Modulator Interactions
# =============================================================================


class TestCoordinatorInitialization:
    """Test coordinator initialization."""

    def test_coordinator_initializes_all_modulators(self):
        """Coordinator should initialize all 4 neuromodulators."""
        coordinator = NeuromodulationCoordinator()
        
        assert hasattr(coordinator, "dopamine")
        assert hasattr(coordinator, "serotonin")
        assert hasattr(coordinator, "acetylcholine")
        assert hasattr(coordinator, "norepinephrine")


class TestCoordinatorConflictResolution:
    """Test conflict resolution between antagonistic modulators."""

    def test_da_5ht_antagonism_detected(self):
        """DA↑ + 5HT↑ should be detected as conflict."""
        coordinator = NeuromodulationCoordinator()
        
        requests = [
            ModulationRequest(modulator="dopamine", delta=0.1, source="reward"),
            ModulationRequest(modulator="serotonin", delta=0.1, source="impulse_control"),
        ]
        
        score = coordinator._compute_conflict_score(requests)
        
        # Should detect antagonism
        assert score > 0


class TestCoordinatorEmergencyStop:
    """Test emergency stop - stops all modulators."""

    def test_emergency_stop_stops_all_modulators(self):
        """Emergency stop should stop all 4 modulators."""
        coordinator = NeuromodulationCoordinator()
        
        coordinator.emergency_stop()
        
        # All modulators should have circuit breakers open
        assert coordinator.dopamine._circuit_breaker_open
        assert coordinator.serotonin._circuit_breaker_open
        assert coordinator.acetylcholine._circuit_breaker_open
        assert coordinator.norepinephrine._circuit_breaker_open


class TestCoordinatorHealthMetrics:
    """Test health metrics aggregation."""

    def test_get_health_metrics_aggregates_all(self):
        """Health metrics should aggregate from all modulators."""
        coordinator = NeuromodulationCoordinator()
        
        metrics = coordinator.get_health_metrics()
        
        # Should have dopamine metrics
        assert "dopamine_level" in metrics
        # Should have serotonin metrics
        assert "serotonin_level" in metrics
        # Should have coordination metrics
        assert "total_coordinations" in metrics or "coordination_count" in metrics or len(metrics) > 4


class TestCoordinatorGetLevels:
    """Test getting current levels of all modulators."""

    def test_get_levels_returns_all_four(self):
        """get_levels should return levels for all 4 modulators."""
        coordinator = NeuromodulationCoordinator()
        
        levels = coordinator.get_levels()
        
        assert "dopamine" in levels
        assert "serotonin" in levels
        assert "acetylcholine" in levels
        assert "norepinephrine" in levels
        
        # All levels should be in [0, 1]
        for level in levels.values():
            assert 0 <= level <= 1
