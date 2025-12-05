"""
MCEA Models - Data structures for arousal control system.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class ArousalLevel(Enum):
    """Classification of arousal states."""

    SLEEP = "sleep"  # 0.0-0.2: Minimal/no consciousness
    DROWSY = "drowsy"  # 0.2-0.4: Reduced awareness
    RELAXED = "relaxed"  # 0.4-0.6: Normal baseline
    ALERT = "alert"  # 0.6-0.8: Heightened awareness
    HYPERALERT = "hyperalert"  # 0.8-1.0: Stress/panic state


@dataclass
class ArousalState:
    """Current arousal state - represents global excitability/wakefulness level."""

    arousal: float = 0.6  # Core arousal value (0.0 - 1.0), default: RELAXED
    level: ArousalLevel = field(default=ArousalLevel.RELAXED, init=False)

    # Contributing factors (for transparency)
    baseline_arousal: float = 0.6
    need_contribution: float = 0.0  # From MMEI needs
    external_contribution: float = 0.0  # From threats/tasks
    temporal_contribution: float = 0.0  # From stress buildup
    circadian_contribution: float = 0.0  # From time-of-day

    # ESGT threshold (computed from arousal)
    esgt_salience_threshold: float = 0.70

    # Metadata
    timestamp: float = field(default_factory=time.time)
    time_in_current_level_seconds: float = 0.0

    def __post_init__(self):
        """Automatically classify level based on arousal value."""
        self.level = self._classify_arousal_level(self.arousal)

    def _classify_arousal_level(self, arousal: float) -> ArousalLevel:
        """Classify arousal level based on value."""
        if arousal <= 0.2:
            return ArousalLevel.SLEEP
        if arousal <= 0.4:
            return ArousalLevel.DROWSY
        if arousal <= 0.6:
            return ArousalLevel.RELAXED
        if arousal <= 0.8:
            return ArousalLevel.ALERT
        return ArousalLevel.HYPERALERT

    def get_arousal_factor(self) -> float:
        """Get arousal multiplication factor for threshold modulation."""
        return 0.5 + (self.arousal * 1.5)

    def compute_effective_threshold(self, base_threshold: float = 0.70) -> float:
        """Compute effective ESGT salience threshold."""
        factor = self.get_arousal_factor()
        return base_threshold / factor

    def __repr__(self) -> str:
        return (
            f"ArousalState(arousal={self.arousal:.2f}, level={self.level.value}, "
            f"threshold={self.esgt_salience_threshold:.2f})"
        )


@dataclass
class ArousalModulation:
    """Request to modulate arousal from external systems."""

    source: str  # What requested modulation
    delta: float  # Change in arousal (-1.0 to +1.0)
    duration_seconds: float = 0.0  # How long effect lasts (0 = instant)
    priority: int = 1  # Higher priority overrides
    timestamp: float = field(default_factory=time.time)

    def is_expired(self) -> bool:
        """Check if modulation has expired."""
        if self.duration_seconds == 0.0:
            return True
        return (time.time() - self.timestamp) > self.duration_seconds

    def get_current_delta(self) -> float:
        """Get current modulation delta (decays over time if duration-based)."""
        if self.duration_seconds == 0.0:
            return self.delta
        elapsed = time.time() - self.timestamp
        if elapsed >= self.duration_seconds:
            return 0.0
        remaining_fraction = 1.0 - (elapsed / self.duration_seconds)
        return self.delta * remaining_fraction


@dataclass
class ArousalConfig:
    """Configuration for arousal controller."""

    baseline_arousal: float = 0.6  # RELAXED default
    update_interval_ms: float = 100.0  # 10 Hz

    # Time constants (how fast arousal changes)
    arousal_increase_rate: float = 0.05  # Per second when increasing
    arousal_decrease_rate: float = 0.02  # Per second when decreasing (slower)

    # Need influence (how much MMEI needs affect arousal)
    repair_need_weight: float = 0.3
    rest_need_weight: float = -0.2
    efficiency_need_weight: float = 0.1
    connectivity_need_weight: float = 0.15

    # Stress buildup
    stress_buildup_rate: float = 0.01  # Per second under high load
    stress_recovery_rate: float = 0.005  # Per second when relaxed

    # ESGT refractory period
    esgt_refractory_arousal_drop: float = 0.1
    esgt_refractory_duration_seconds: float = 5.0

    # Circadian rhythm (optional)
    enable_circadian: bool = False
    circadian_amplitude: float = 0.1

    # Arousal bounds
    min_arousal: float = 0.0
    max_arousal: float = 1.0
