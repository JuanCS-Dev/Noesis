"""
MMEI Rate Limiter - Goal Generation Safety
==========================================

This module implements rate limiting for goal generation to prevent MMEI
from overwhelming downstream systems (ESGT/HCL) with excessive goals.

FASE VII (Safety Hardening):
----------------------------
Uses sliding window algorithm for smooth enforcement without burst allowance.
This ensures MMEI operates within safe bounds even under high stress.

Theoretical Foundation:
-----------------------
Biological systems have built-in rate limiting mechanisms:
- Refractory periods in neurons (prevent over-firing)
- Habituation in sensory systems (prevent over-reaction)
- Inhibitory feedback loops (prevent runaway activation)

MMEI's rate limiter provides similar protection, ensuring the system cannot
generate goals faster than downstream components can process them.

Implementation:
---------------
- Sliding window: Goals tracked over 60-second window
- Hard limit: max_per_minute cannot be exceeded
- No burst allowance: Smooth enforcement across window
"""

from __future__ import annotations

import time
from collections import deque


class RateLimiter:
    """
    Sliding window rate limiter for goal generation.

    Prevents MMEI from overwhelming downstream systems (ESGT/HCL) with
    excessive goal generation. Uses sliding window algorithm for smooth
    enforcement (no burst allowance).

    HARD LIMIT: Goals per minute cannot exceed max_per_minute.
    """

    def __init__(self, max_per_minute: int = 5):
        """
        Args:
            max_per_minute: Maximum goals allowed per 60-second window
        """
        self.max_per_minute = max_per_minute
        self.window_seconds = 60.0
        self.timestamps: deque = deque(maxlen=max_per_minute)

    def allow(self) -> bool:
        """
        Check if a new goal can be generated.

        Returns:
            True if within rate limit, False if limit exceeded
        """
        now = time.time()

        # Remove timestamps outside window
        while self.timestamps and now - self.timestamps[0] > self.window_seconds:
            self.timestamps.popleft()

        # Check if we're at capacity
        if len(self.timestamps) >= self.max_per_minute:
            return False

        # Record this timestamp
        self.timestamps.append(now)
        return True

    def get_current_rate(self) -> int:
        """Get current goals per minute in sliding window."""
        now = time.time()
        # Count timestamps within window
        return sum(1 for t in self.timestamps if now - t <= self.window_seconds)
