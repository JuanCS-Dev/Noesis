"""
MCEA Safety - Rate limiting and bounds enforcement for arousal control.

FASE VII (Safety Hardening): Arousal Rate Limiting & Bounds Enforcement
"""

from __future__ import annotations

import numpy as np


# Hard limits for MCEA safety
MAX_AROUSAL_DELTA_PER_SECOND = 0.20  # Hard limit on arousal rate of change
AROUSAL_SATURATION_THRESHOLD_SECONDS = 10.0  # Time at 0.0 or 1.0 = saturation
AROUSAL_OSCILLATION_WINDOW = 20  # Track last 20 arousal values
AROUSAL_OSCILLATION_THRESHOLD = 0.15  # StdDev >0.15 = unstable oscillation


class ArousalRateLimiter:
    """
    Enforces maximum rate of change for arousal value.

    HARD LIMIT: Arousal can change at most ±0.20 per second.
    """

    def __init__(self, max_delta_per_second: float = 0.20):
        """Initialize with max delta per second."""
        self.max_delta_per_second = max_delta_per_second
        self.last_arousal: float | None = None
        self.last_update_time: float | None = None

    def limit(self, new_arousal: float, current_time: float) -> float:
        """Apply rate limiting to new arousal value."""
        if self.last_arousal is None or self.last_update_time is None:
            self.last_arousal = new_arousal
            self.last_update_time = current_time
            return new_arousal

        elapsed = current_time - self.last_update_time
        if elapsed <= 0:
            return self.last_arousal

        max_change = self.max_delta_per_second * elapsed
        requested_change = new_arousal - self.last_arousal

        if abs(requested_change) > max_change:
            limited_change = max_change if requested_change > 0 else -max_change
            limited_arousal = self.last_arousal + limited_change
        else:
            limited_arousal = new_arousal

        self.last_arousal = limited_arousal
        self.last_update_time = current_time
        return limited_arousal


class ArousalBoundEnforcer:
    """
    Enforces hard bounds [0.0, 1.0] on arousal value.

    HARD LIMIT: Arousal must always be in [0.0, 1.0].
    """

    @staticmethod
    def enforce(arousal: float) -> float:
        """Clamp arousal to [0.0, 1.0]."""
        return float(np.clip(arousal, 0.0, 1.0))
