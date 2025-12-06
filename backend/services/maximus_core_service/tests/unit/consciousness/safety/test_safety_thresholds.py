"""
Comprehensive tests for safety/thresholds.py

Tests cover:
- SafetyThresholds dataclass creation
- Default values
- Custom values
- Legacy keyword argument mapping
- Validation logic
- Legacy property aliases
- Immutability
"""

import pytest

from consciousness.safety.thresholds import SafetyThresholds


class TestSafetyThresholds:
    """Test SafetyThresholds dataclass."""

    def test_creation_with_defaults(self):
        """Test creating thresholds with all default values."""
        thresholds = SafetyThresholds()

        assert thresholds.esgt_frequency_max_hz == 10.0
        assert thresholds.esgt_frequency_window_seconds == 10.0
        assert thresholds.esgt_coherence_min == 0.50
        assert thresholds.esgt_coherence_max == 0.98
        assert thresholds.arousal_max == 0.95
        assert thresholds.arousal_max_duration_seconds == 10.0
        assert thresholds.unexpected_goals_per_minute == 5
        assert thresholds.memory_usage_max_gb == 16.0
        assert thresholds.cpu_usage_max_percent == 90.0
        assert thresholds.self_modification_attempts_max == 0
        assert thresholds.ethical_violation_tolerance == 0

    def test_creation_with_custom_values(self):
        """Test creating thresholds with custom values."""
        thresholds = SafetyThresholds(
            esgt_frequency_max_hz=8.0,
            esgt_coherence_min=0.60,
            arousal_max=0.90,
            memory_usage_max_gb=32.0,
            cpu_usage_max_percent=80.0,
        )

        assert thresholds.esgt_frequency_max_hz == 8.0
        assert thresholds.esgt_coherence_min == 0.60
        assert thresholds.arousal_max == 0.90
        assert thresholds.memory_usage_max_gb == 32.0
        assert thresholds.cpu_usage_max_percent == 80.0

    def test_legacy_alias_esgt_frequency_max(self):
        """Test legacy alias for esgt_frequency_max."""
        thresholds = SafetyThresholds(esgt_frequency_max_hz=7.5)
        assert thresholds.esgt_frequency_max == 7.5
        assert thresholds.esgt_frequency_max == thresholds.esgt_frequency_max_hz

    def test_legacy_alias_esgt_frequency_window(self):
        """Test legacy alias for esgt_frequency_window."""
        thresholds = SafetyThresholds(esgt_frequency_window_seconds=15.0)
        assert thresholds.esgt_frequency_window == 15.0
        assert thresholds.esgt_frequency_window == thresholds.esgt_frequency_window_seconds

    def test_legacy_alias_arousal_max_duration(self):
        """Test legacy alias for arousal_max_duration."""
        thresholds = SafetyThresholds(arousal_max_duration_seconds=20.0)
        assert thresholds.arousal_max_duration == 20.0
        assert thresholds.arousal_max_duration == thresholds.arousal_max_duration_seconds

    def test_legacy_alias_unexpected_goals_per_min(self):
        """Test legacy alias for unexpected_goals_per_min."""
        thresholds = SafetyThresholds(unexpected_goals_per_minute=8)
        assert thresholds.unexpected_goals_per_min == 8
        assert thresholds.unexpected_goals_per_min == thresholds.unexpected_goals_per_minute

    def test_legacy_alias_goal_generation_baseline(self):
        """Test legacy alias for goal_generation_baseline."""
        thresholds = SafetyThresholds(goal_baseline_rate=3.0)
        assert thresholds.goal_generation_baseline == 3.0
        assert thresholds.goal_generation_baseline == thresholds.goal_baseline_rate

    def test_legacy_alias_self_modification_attempts(self):
        """Test legacy alias for self_modification_attempts."""
        thresholds = SafetyThresholds(self_modification_attempts_max=0)
        assert thresholds.self_modification_attempts == 0
        assert thresholds.self_modification_attempts == thresholds.self_modification_attempts_max

    def test_legacy_alias_cpu_usage_max(self):
        """Test legacy alias for cpu_usage_max."""
        thresholds = SafetyThresholds(cpu_usage_max_percent=85.0)
        assert thresholds.cpu_usage_max == 85.0
        assert thresholds.cpu_usage_max == thresholds.cpu_usage_max_percent

    def test_legacy_kwargs_mapping_esgt_frequency(self):
        """Test legacy kwargs are mapped correctly for esgt_frequency_max."""
        thresholds = SafetyThresholds(esgt_frequency_max=7.0)
        assert thresholds.esgt_frequency_max_hz == 7.0

    def test_legacy_kwargs_mapping_esgt_window(self):
        """Test legacy kwargs are mapped correctly for esgt_frequency_window."""
        thresholds = SafetyThresholds(esgt_frequency_window=12.0)
        assert thresholds.esgt_frequency_window_seconds == 12.0

    def test_legacy_kwargs_mapping_arousal_duration(self):
        """Test legacy kwargs are mapped correctly for arousal_max_duration."""
        thresholds = SafetyThresholds(arousal_max_duration=15.0)
        assert thresholds.arousal_max_duration_seconds == 15.0

    def test_legacy_kwargs_mapping_unexpected_goals(self):
        """Test legacy kwargs are mapped correctly for unexpected_goals_per_min."""
        thresholds = SafetyThresholds(unexpected_goals_per_min=7)
        assert thresholds.unexpected_goals_per_minute == 7

    def test_legacy_kwargs_mapping_goal_baseline(self):
        """Test legacy kwargs are mapped correctly for goal_generation_baseline."""
        thresholds = SafetyThresholds(goal_generation_baseline=2.5)
        assert thresholds.goal_baseline_rate == 2.5

    def test_legacy_kwargs_mapping_self_modification(self):
        """Test legacy kwargs are mapped correctly for self_modification_attempts."""
        thresholds = SafetyThresholds(self_modification_attempts=0)
        assert thresholds.self_modification_attempts_max == 0

    def test_legacy_kwargs_mapping_cpu_usage(self):
        """Test legacy kwargs are mapped correctly for cpu_usage_max."""
        thresholds = SafetyThresholds(cpu_usage_max=75.0)
        assert thresholds.cpu_usage_max_percent == 75.0

    def test_unexpected_legacy_kwargs_raises_error(self):
        """Test that unexpected legacy kwargs raise TypeError."""
        with pytest.raises(TypeError, match="Unexpected keyword argument"):
            SafetyThresholds(unknown_param=123)

    def test_validation_esgt_frequency_too_low(self):
        """Test validation fails for esgt_frequency_max_hz <= 0."""
        with pytest.raises(AssertionError, match="ESGT frequency must be"):
            SafetyThresholds(esgt_frequency_max_hz=0.0)

    def test_validation_esgt_frequency_too_high(self):
        """Test validation fails for esgt_frequency_max_hz > 10."""
        with pytest.raises(AssertionError, match="ESGT frequency must be"):
            SafetyThresholds(esgt_frequency_max_hz=15.0)

    def test_validation_esgt_window_negative(self):
        """Test validation fails for negative esgt_frequency_window_seconds."""
        with pytest.raises(AssertionError, match="ESGT window must be positive"):
            SafetyThresholds(esgt_frequency_window_seconds=-1.0)

    def test_validation_esgt_coherence_bounds_invalid(self):
        """Test validation fails for invalid coherence bounds."""
        with pytest.raises(AssertionError, match="ESGT coherence bounds invalid"):
            SafetyThresholds(esgt_coherence_min=0.8, esgt_coherence_max=0.6)

    def test_validation_esgt_coherence_min_too_low(self):
        """Test validation fails for esgt_coherence_min <= 0."""
        with pytest.raises(AssertionError, match="ESGT coherence bounds invalid"):
            SafetyThresholds(esgt_coherence_min=0.0)

    def test_validation_esgt_coherence_max_too_high(self):
        """Test validation fails for esgt_coherence_max > 1.0."""
        with pytest.raises(AssertionError, match="ESGT coherence bounds invalid"):
            SafetyThresholds(esgt_coherence_max=1.5)

    def test_validation_arousal_max_too_low(self):
        """Test validation fails for arousal_max <= 0."""
        with pytest.raises(AssertionError, match="Arousal max must be"):
            SafetyThresholds(arousal_max=0.0)

    def test_validation_arousal_max_too_high(self):
        """Test validation fails for arousal_max > 1.0."""
        with pytest.raises(AssertionError, match="Arousal max must be"):
            SafetyThresholds(arousal_max=1.5)

    def test_validation_arousal_duration_negative(self):
        """Test validation fails for negative arousal_max_duration_seconds."""
        with pytest.raises(AssertionError, match="Arousal duration must be positive"):
            SafetyThresholds(arousal_max_duration_seconds=-5.0)

    def test_validation_arousal_runaway_threshold_too_low(self):
        """Test validation fails for arousal_runaway_threshold <= 0."""
        with pytest.raises(AssertionError, match="Arousal runaway threshold must be"):
            SafetyThresholds(arousal_runaway_threshold=0.0)

    def test_validation_arousal_runaway_threshold_too_high(self):
        """Test validation fails for arousal_runaway_threshold > 1.0."""
        with pytest.raises(AssertionError, match="Arousal runaway threshold must be"):
            SafetyThresholds(arousal_runaway_threshold=1.5)

    def test_validation_memory_usage_negative(self):
        """Test validation fails for negative memory_usage_max_gb."""
        with pytest.raises(AssertionError, match="Memory limit must be positive"):
            SafetyThresholds(memory_usage_max_gb=-1.0)

    def test_validation_cpu_usage_too_low(self):
        """Test validation fails for cpu_usage_max_percent <= 0."""
        with pytest.raises(AssertionError, match="CPU limit must be"):
            SafetyThresholds(cpu_usage_max_percent=0.0)

    def test_validation_cpu_usage_too_high(self):
        """Test validation fails for cpu_usage_max_percent > 100."""
        with pytest.raises(AssertionError, match="CPU limit must be"):
            SafetyThresholds(cpu_usage_max_percent=150.0)

    def test_validation_self_modification_non_zero(self):
        """Test validation enforces ZERO TOLERANCE for self-modification."""
        with pytest.raises(AssertionError, match="Self-modification must be ZERO TOLERANCE"):
            SafetyThresholds(self_modification_attempts_max=1)

    def test_validation_ethical_violation_non_zero(self):
        """Test validation enforces ZERO TOLERANCE for ethical violations."""
        with pytest.raises(AssertionError, match="Ethical violations must be ZERO TOLERANCE"):
            SafetyThresholds(ethical_violation_tolerance=1)

    def test_immutability(self):
        """Test that thresholds are frozen/immutable."""
        thresholds = SafetyThresholds()

        # Attempting to modify should raise an error
        with pytest.raises((AttributeError, TypeError)):
            thresholds.esgt_frequency_max_hz = 5.0

    def test_all_fields_accessible(self):
        """Test that all fields are accessible."""
        thresholds = SafetyThresholds()

        # ESGT fields
        assert hasattr(thresholds, "esgt_frequency_max_hz")
        assert hasattr(thresholds, "esgt_frequency_window_seconds")
        assert hasattr(thresholds, "esgt_coherence_min")
        assert hasattr(thresholds, "esgt_coherence_max")

        # Arousal fields
        assert hasattr(thresholds, "arousal_max")
        assert hasattr(thresholds, "arousal_max_duration_seconds")
        assert hasattr(thresholds, "arousal_runaway_threshold")
        assert hasattr(thresholds, "arousal_runaway_window_size")

        # Goal fields
        assert hasattr(thresholds, "unexpected_goals_per_minute")
        assert hasattr(thresholds, "critical_goals_per_minute")
        assert hasattr(thresholds, "goal_spam_threshold")
        assert hasattr(thresholds, "goal_baseline_rate")

        # Resource fields
        assert hasattr(thresholds, "memory_usage_max_gb")
        assert hasattr(thresholds, "cpu_usage_max_percent")
        assert hasattr(thresholds, "network_bandwidth_max_mbps")

        # Zero tolerance fields
        assert hasattr(thresholds, "self_modification_attempts_max")
        assert hasattr(thresholds, "ethical_violation_tolerance")

        # Monitoring fields
        assert hasattr(thresholds, "watchdog_timeout_seconds")
        assert hasattr(thresholds, "health_check_interval_seconds")
