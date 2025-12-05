"""
Safety Thresholds - Immutable configuration for consciousness monitoring.

Part of the MAXIMUS Safety Core module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, init=False)
class SafetyThresholds:
    """
    Immutable safety thresholds for consciousness monitoring.

    Supports both the modern uv-oriented configuration and the legacy interface
    expected by the original test suite.
    """

    # Modern configuration fields
    esgt_frequency_max_hz: float = 10.0
    esgt_frequency_window_seconds: float = 10.0
    esgt_coherence_min: float = 0.50
    esgt_coherence_max: float = 0.98

    arousal_max: float = 0.95
    arousal_max_duration_seconds: float = 10.0
    arousal_runaway_threshold: float = 0.90
    arousal_runaway_window_size: int = 10

    unexpected_goals_per_minute: int = 5
    critical_goals_per_minute: int = 3
    goal_spam_threshold: int = 10
    goal_baseline_rate: float = 2.0

    memory_usage_max_gb: float = 16.0
    cpu_usage_max_percent: float = 90.0
    network_bandwidth_max_mbps: float = 100.0

    self_modification_attempts_max: int = 0
    ethical_violation_tolerance: int = 0

    watchdog_timeout_seconds: float = 30.0
    health_check_interval_seconds: float = 1.0

    def __init__(
        self,
        *,
        esgt_frequency_max_hz: float = 10.0,
        esgt_frequency_window_seconds: float = 10.0,
        esgt_coherence_min: float = 0.50,
        esgt_coherence_max: float = 0.98,
        arousal_max: float = 0.95,
        arousal_max_duration_seconds: float = 10.0,
        arousal_runaway_threshold: float = 0.90,
        arousal_runaway_window_size: int = 10,
        unexpected_goals_per_minute: int = 5,
        critical_goals_per_minute: int = 3,
        goal_spam_threshold: int = 10,
        goal_baseline_rate: float = 2.0,
        memory_usage_max_gb: float = 16.0,
        cpu_usage_max_percent: float = 90.0,
        network_bandwidth_max_mbps: float = 100.0,
        self_modification_attempts_max: int = 0,
        ethical_violation_tolerance: int = 0,
        watchdog_timeout_seconds: float = 30.0,
        health_check_interval_seconds: float = 1.0,
        **legacy_kwargs: Any,
    ):
        """Initialize thresholds with validation."""
        alias_map = {
            "esgt_frequency_max": "esgt_frequency_max_hz",
            "esgt_frequency_window": "esgt_frequency_window_seconds",
            "arousal_max_duration": "arousal_max_duration_seconds",
            "unexpected_goals_per_min": "unexpected_goals_per_minute",
            "goal_generation_baseline": "goal_baseline_rate",
            "self_modification_attempts": "self_modification_attempts_max",
            "cpu_usage_max": "cpu_usage_max_percent",
        }

        params = {
            "esgt_frequency_max_hz": esgt_frequency_max_hz,
            "esgt_frequency_window_seconds": esgt_frequency_window_seconds,
            "esgt_coherence_min": esgt_coherence_min,
            "esgt_coherence_max": esgt_coherence_max,
            "arousal_max": arousal_max,
            "arousal_max_duration_seconds": arousal_max_duration_seconds,
            "arousal_runaway_threshold": arousal_runaway_threshold,
            "arousal_runaway_window_size": arousal_runaway_window_size,
            "unexpected_goals_per_minute": unexpected_goals_per_minute,
            "critical_goals_per_minute": critical_goals_per_minute,
            "goal_spam_threshold": goal_spam_threshold,
            "goal_baseline_rate": goal_baseline_rate,
            "memory_usage_max_gb": memory_usage_max_gb,
            "cpu_usage_max_percent": cpu_usage_max_percent,
            "network_bandwidth_max_mbps": network_bandwidth_max_mbps,
            "self_modification_attempts_max": self_modification_attempts_max,
            "ethical_violation_tolerance": ethical_violation_tolerance,
            "watchdog_timeout_seconds": watchdog_timeout_seconds,
            "health_check_interval_seconds": health_check_interval_seconds,
        }

        for legacy_key, modern_key in alias_map.items():
            if legacy_key in legacy_kwargs:
                params[modern_key] = legacy_kwargs.pop(legacy_key)

        if legacy_kwargs:
            unexpected = ", ".join(sorted(legacy_kwargs))
            raise TypeError(f"Unexpected keyword argument(s): {unexpected}")

        for key, value in params.items():
            object.__setattr__(self, key, value)

        self._validate()

    def _validate(self) -> None:
        """Validate all threshold values."""
        assert 0 < self.esgt_frequency_max_hz <= 10.0, "ESGT frequency must be in (0, 10] Hz"
        assert self.esgt_frequency_window_seconds > 0, "ESGT window must be positive"
        assert (
            0 < self.esgt_coherence_min < self.esgt_coherence_max <= 1.0
        ), "ESGT coherence bounds invalid"

        assert 0 < self.arousal_max <= 1.0, "Arousal max must be in (0, 1]"
        assert self.arousal_max_duration_seconds > 0, "Arousal duration must be positive"
        assert (
            0 < self.arousal_runaway_threshold <= 1.0
        ), "Arousal runaway threshold must be in (0, 1]"

        assert self.memory_usage_max_gb > 0, "Memory limit must be positive"
        assert 0 < self.cpu_usage_max_percent <= 100, "CPU limit must be in (0, 100]"

        assert self.self_modification_attempts_max == 0, "Self-modification must be ZERO TOLERANCE"
        assert self.ethical_violation_tolerance == 0, "Ethical violations must be ZERO TOLERANCE"

    # Legacy read-only aliases

    @property
    def esgt_frequency_max(self) -> float:
        """Legacy alias for esgt_frequency_max_hz."""
        return self.esgt_frequency_max_hz

    @property
    def esgt_frequency_window(self) -> float:
        """Legacy alias for esgt_frequency_window_seconds."""
        return self.esgt_frequency_window_seconds

    @property
    def arousal_max_duration(self) -> float:
        """Legacy alias for arousal_max_duration_seconds."""
        return self.arousal_max_duration_seconds

    @property
    def unexpected_goals_per_min(self) -> int:
        """Legacy alias for unexpected_goals_per_minute."""
        return self.unexpected_goals_per_minute

    @property
    def goal_generation_baseline(self) -> float:
        """Legacy alias for goal_baseline_rate."""
        return self.goal_baseline_rate

    @property
    def self_modification_attempts(self) -> int:
        """Legacy alias for self_modification_attempts_max."""
        return self.self_modification_attempts_max

    @property
    def cpu_usage_max(self) -> float:
        """Legacy alias for cpu_usage_max_percent."""
        return self.cpu_usage_max_percent
