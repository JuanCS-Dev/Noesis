"""Tests for esgt/kuramoto_models.py"""

import time

import numpy as np

from consciousness.esgt.kuramoto_models import (
    OscillatorConfig,
    OscillatorState,
    PhaseCoherence,
    SynchronizationDynamics,
)


class TestOscillatorState:
    """Test OscillatorState enum."""

    def test_all_states_exist(self):
        """Test all oscillator states."""
        assert OscillatorState.IDLE.value == "idle"
        assert OscillatorState.COUPLING.value == "coupling"
        assert OscillatorState.SYNCHRONIZED.value == "synchronized"
        assert OscillatorState.DESYNCHRONIZING.value == "desynchronizing"


class TestOscillatorConfig:
    """Test OscillatorConfig dataclass."""

    def test_creation_defaults(self):
        """Test creating with defaults."""
        config = OscillatorConfig()
        
        assert config.natural_frequency == 40.0
        assert config.coupling_strength == 20.0
        assert config.phase_noise == 0.001
        assert config.integration_method == "rk4"

    def test_creation_custom(self):
        """Test creating with custom values."""
        config = OscillatorConfig(
            natural_frequency=50.0,
            coupling_strength=30.0,
            phase_noise=0.002,
            integration_method="euler",
        )
        
        assert config.natural_frequency == 50.0
        assert config.coupling_strength == 30.0
        assert config.phase_noise == 0.002
        assert config.integration_method == "euler"


class TestPhaseCoherence:
    """Test PhaseCoherence dataclass."""

    def test_creation(self):
        """Test creating phase coherence."""
        coherence = PhaseCoherence(
            order_parameter=0.75,
            mean_phase=1.57,
            phase_variance=0.2,
            coherence_quality="conscious",
        )
        
        assert coherence.order_parameter == 0.75
        assert coherence.mean_phase == 1.57
        assert coherence.phase_variance == 0.2
        assert coherence.coherence_quality == "conscious"

    def test_creation_with_timestamp(self):
        """Test creating with custom timestamp."""
        ts = time.time()
        coherence = PhaseCoherence(
            order_parameter=0.5,
            mean_phase=0.0,
            phase_variance=0.5,
            coherence_quality="preconscious",
            timestamp=ts,
        )
        
        assert coherence.timestamp == ts

    def test_is_conscious_level_true(self):
        """Test conscious level check - true."""
        coherence = PhaseCoherence(
            order_parameter=0.75,
            mean_phase=0.0,
            phase_variance=0.1,
            coherence_quality="conscious",
        )
        
        assert coherence.is_conscious_level() is True

    def test_is_conscious_level_false(self):
        """Test conscious level check - false."""
        coherence = PhaseCoherence(
            order_parameter=0.50,
            mean_phase=0.0,
            phase_variance=0.3,
            coherence_quality="preconscious",
        )
        
        assert coherence.is_conscious_level() is False

    def test_is_conscious_level_boundary(self):
        """Test conscious level check - at boundary."""
        coherence = PhaseCoherence(
            order_parameter=0.70,
            mean_phase=0.0,
            phase_variance=0.2,
            coherence_quality="conscious",
        )
        
        assert coherence.is_conscious_level() is True

    def test_get_quality_score_unconscious(self):
        """Test quality score for unconscious level."""
        coherence = PhaseCoherence(
            order_parameter=0.15,
            mean_phase=0.0,
            phase_variance=0.5,
            coherence_quality="unconscious",
        )
        
        score = coherence.get_quality_score()
        assert 0.0 <= score <= 0.25

    def test_get_quality_score_preconscious(self):
        """Test quality score for preconscious level."""
        coherence = PhaseCoherence(
            order_parameter=0.50,
            mean_phase=0.0,
            phase_variance=0.3,
            coherence_quality="preconscious",
        )
        
        score = coherence.get_quality_score()
        assert 0.25 < score < 0.75

    def test_get_quality_score_conscious(self):
        """Test quality score for conscious level."""
        coherence = PhaseCoherence(
            order_parameter=0.80,
            mean_phase=0.0,
            phase_variance=0.1,
            coherence_quality="conscious",
        )
        
        score = coherence.get_quality_score()
        assert 0.75 <= score <= 1.0

    def test_get_quality_score_deep(self):
        """Test quality score for deep coherence."""
        coherence = PhaseCoherence(
            order_parameter=0.95,
            mean_phase=0.0,
            phase_variance=0.05,
            coherence_quality="deep",
        )
        
        score = coherence.get_quality_score()
        assert score > 0.9


class TestSynchronizationDynamics:
    """Test SynchronizationDynamics dataclass."""

    def test_creation_defaults(self):
        """Test creating with defaults."""
        dynamics = SynchronizationDynamics()
        
        assert dynamics.coherence_history == []
        assert dynamics.time_to_sync is None
        assert dynamics.max_coherence == 0.0
        assert dynamics.sustained_duration == 0.0
        assert dynamics.dissolution_rate == 0.0

    def test_creation_with_values(self):
        """Test creating with custom values."""
        dynamics = SynchronizationDynamics(
            coherence_history=[0.3, 0.5, 0.7],
            time_to_sync=0.150,
            max_coherence=0.85,
            sustained_duration=0.200,
        )
        
        assert len(dynamics.coherence_history) == 3
        assert dynamics.time_to_sync == 0.150
        assert dynamics.max_coherence == 0.85

    def test_add_coherence_sample(self):
        """Test adding coherence sample."""
        dynamics = SynchronizationDynamics()
        
        dynamics.add_coherence_sample(0.5, 1000.0)
        
        assert len(dynamics.coherence_history) == 1
        assert dynamics.coherence_history[0] == 0.5

    def test_add_coherence_sample_updates_max(self):
        """Test that adding sample updates max_coherence."""
        dynamics = SynchronizationDynamics()
        
        dynamics.add_coherence_sample(0.5, 1000.0)
        dynamics.add_coherence_sample(0.8, 1001.0)
        dynamics.add_coherence_sample(0.6, 1002.0)
        
        assert dynamics.max_coherence == 0.8

    def test_add_coherence_sample_multiple(self):
        """Test adding multiple coherence samples."""
        dynamics = SynchronizationDynamics()
        
        for i, coherence in enumerate([0.3, 0.5, 0.7, 0.8, 0.75]):
            dynamics.add_coherence_sample(coherence, 1000.0 + i)
        
        assert len(dynamics.coherence_history) == 5
        assert dynamics.max_coherence == 0.8

    def test_compute_dissolution_rate_insufficient_data(self):
        """Test dissolution rate with insufficient data."""
        dynamics = SynchronizationDynamics()
        
        for i in range(5):
            dynamics.add_coherence_sample(0.5, 1000.0 + i)
        
        rate = dynamics.compute_dissolution_rate()
        assert rate == 0.0

    def test_compute_dissolution_rate_with_data(self):
        """Test dissolution rate with sufficient data."""
        dynamics = SynchronizationDynamics()
        
        # Add 15 samples with decreasing coherence (dissolution)
        for i in range(15):
            coherence = 0.9 - i * 0.05
            dynamics.add_coherence_sample(coherence, 1000.0 + i * 0.005)
        
        rate = dynamics.compute_dissolution_rate()
        assert rate > 0  # Should be positive (decay)

    def test_compute_dissolution_rate_increasing(self):
        """Test dissolution rate with increasing coherence."""
        dynamics = SynchronizationDynamics()
        
        # Add samples with increasing coherence
        for i in range(15):
            coherence = 0.3 + i * 0.04
            dynamics.add_coherence_sample(coherence, 1000.0 + i * 0.005)
        
        rate = dynamics.compute_dissolution_rate()
        assert rate < 0  # Should be negative (building up)

    def test_compute_dissolution_rate_stable(self):
        """Test dissolution rate with stable coherence."""
        dynamics = SynchronizationDynamics()
        
        # Add samples with constant coherence
        for i in range(15):
            dynamics.add_coherence_sample(0.7, 1000.0 + i * 0.005)
        
        rate = dynamics.compute_dissolution_rate()
        assert abs(rate) < 0.1  # Should be near zero
