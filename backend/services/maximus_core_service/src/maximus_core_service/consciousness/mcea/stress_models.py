"""Stress Monitoring Models - Data structures for stress testing and response tracking."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class StressLevel(Enum):
    """Classification of stress intensity (0.0-1.0 range)."""

    NONE = "none"  # 0.0-0.2
    MILD = "mild"  # 0.2-0.4
    MODERATE = "moderate"  # 0.4-0.6
    SEVERE = "severe"  # 0.6-0.8
    CRITICAL = "critical"  # 0.8-1.0


class StressType(Enum):
    """Types of stress that can be applied."""

    COMPUTATIONAL_LOAD = "computational_load"  # High CPU/memory
    ERROR_INJECTION = "error_injection"  # System failures
    NETWORK_DEGRADATION = "network_degradation"  # Latency/loss
    AROUSAL_FORCING = "arousal_forcing"  # Forced high arousal
    RAPID_CHANGE = "rapid_change"  # Fast state transitions
    COMBINED = "combined"  # Multiple stressors


@dataclass
class StressResponse:
    """Measured response to stress application."""

    stress_type: StressType
    stress_level: StressLevel

    # Arousal response
    initial_arousal: float
    peak_arousal: float
    final_arousal: float
    arousal_stability_cv: float  # Coefficient of variation

    # Need response
    peak_rest_need: float
    peak_repair_need: float
    peak_efficiency_need: float

    # Goal generation
    goals_generated: int
    goals_satisfied: int
    critical_goals_generated: int

    # ESGT quality
    esgt_events: int
    mean_esgt_coherence: float
    esgt_coherence_degradation: float

    # Recovery metrics
    recovery_time_seconds: float
    full_recovery_achieved: bool

    # Breakdown indicators
    arousal_runaway_detected: bool
    goal_generation_failure: bool
    coherence_collapse: bool

    # Metadata
    duration_seconds: float
    timestamp: float = field(default_factory=time.time)

    def get_resilience_score(self) -> float:
        """Compute overall resilience score (0-100). Higher = better stress handling."""
        score = 100.0

        if self.arousal_runaway_detected:
            score -= 40.0
        if self.goal_generation_failure:
            score -= 20.0
        if self.coherence_collapse:
            score -= 30.0
        if not self.full_recovery_achieved:
            score -= 15.0
        elif self.recovery_time_seconds > 60.0:
            score -= 10.0
        if self.arousal_stability_cv > 0.3:
            score -= 10.0

        return max(score, 0.0)

    def passed_stress_test(self) -> bool:
        """Check if system passed stress test (basic criteria)."""
        return (
            not self.arousal_runaway_detected
            and not self.goal_generation_failure
            and not self.coherence_collapse
            and self.recovery_time_seconds < 120.0
        )

    def __repr__(self) -> str:
        status = "PASS" if self.passed_stress_test() else "FAIL"
        resilience = self.get_resilience_score()
        return (
            f"StressResponse({self.stress_type.value}, level={self.stress_level.value}, "
            f"resilience={resilience:.1f}, status={status})"
        )


@dataclass
class StressTestConfig:
    """Configuration for stress testing."""

    stress_duration_seconds: float = 30.0
    recovery_duration_seconds: float = 60.0

    arousal_runaway_threshold: float = 0.95
    arousal_runaway_duration: float = 10.0
    coherence_collapse_threshold: float = 0.50
    recovery_baseline_tolerance: float = 0.1

    load_stress_cpu_percent: float = 90.0
    error_stress_rate_per_min: float = 20.0
    network_stress_latency_ms: float = 200.0
    arousal_forcing_target: float = 0.9
