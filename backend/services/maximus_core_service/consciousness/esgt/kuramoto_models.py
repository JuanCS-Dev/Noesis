"""Kuramoto Model Data Structures - Phase synchronization models for ESGT coherence."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum

import numpy as np


class OscillatorState(Enum):
    """State of an oscillator during synchronization."""

    IDLE = "idle"
    COUPLING = "coupling"
    SYNCHRONIZED = "synchronized"
    DESYNCHRONIZING = "desynchronizing"


@dataclass
class OscillatorConfig:
    """Configuration for a Kuramoto oscillator."""

    natural_frequency: float = 40.0  # Hz (gamma-band analog)
    coupling_strength: float = 20.0  # K parameter
    phase_noise: float = 0.001  # Additive phase noise
    integration_method: str = "rk4"  # "euler" or "rk4"


@dataclass
class PhaseCoherence:
    """
    Measures phase synchronization quality.

    Order parameter interpretation:
    - r < 0.30: Unconscious (incoherent)
    - 0.30 ≤ r < 0.70: Pre-conscious (partial)
    - r ≥ 0.70: Conscious state (high coherence)
    - r > 0.90: Deep coherence
    """

    order_parameter: float  # r(t) ∈ [0, 1]
    mean_phase: float  # Average phase angle (radians)
    phase_variance: float  # Spread of phases
    coherence_quality: str  # "unconscious", "preconscious", "conscious", "deep"
    timestamp: float = field(default_factory=time.time)

    def is_conscious_level(self) -> bool:
        """Check if coherence is sufficient for conscious binding."""
        return self.order_parameter >= 0.70

    def get_quality_score(self) -> float:
        """Get normalized quality score (0-1)."""
        if self.order_parameter < 0.3:
            return self.order_parameter / 0.3 * 0.25
        if self.order_parameter < 0.7:
            return 0.25 + (self.order_parameter - 0.3) / 0.4 * 0.5
        return 0.75 + (self.order_parameter - 0.7) / 0.3 * 0.25


@dataclass
class SynchronizationDynamics:
    """Tracks synchronization dynamics over time."""

    coherence_history: list[float] = field(default_factory=list)
    time_to_sync: float | None = None
    max_coherence: float = 0.0
    sustained_duration: float = 0.0
    dissolution_rate: float = 0.0

    def add_coherence_sample(self, coherence: float, timestamp: float) -> None:
        """Add coherence measurement to history."""
        self.coherence_history.append(coherence)
        if coherence > self.max_coherence:
            self.max_coherence = coherence

    def compute_dissolution_rate(self) -> float:
        """Compute rate of coherence decay (for graceful dissolution analysis)."""
        if len(self.coherence_history) < 10:
            return 0.0

        recent = self.coherence_history[-10:]
        time_points = np.arange(len(recent)) * 0.005

        x = np.array(time_points, dtype=np.float64)
        y = np.array(recent, dtype=np.float64)
        n = len(x)

        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_x2 = np.sum(x * x)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        decay_rate = -slope

        return float(decay_rate)
