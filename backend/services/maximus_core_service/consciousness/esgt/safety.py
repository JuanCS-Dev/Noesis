"""
ESGT Safety Components
======================

Safety hardening components for ESGT ignition protocol.

FASE VII (Safety Hardening):
This module implements safety mechanisms to prevent ESGT runaway and
ensure stable consciousness operation:

- FrequencyLimiter: Token bucket rate limiting
- Concurrent event tracking
- Degraded mode support
- Circuit breaker integration
"""

from __future__ import annotations

import asyncio
import time


class FrequencyLimiter:
    """
    Hard frequency limiter using token bucket algorithm.

    FASE VII (Safety Hardening):
    Prevents ESGT runaway by enforcing strict frequency bounds.
    """

    def __init__(self, max_frequency_hz: float):
        self.max_frequency = max_frequency_hz
        self.tokens = max_frequency_hz
        self.last_update = time.time()
        self.lock = asyncio.Lock()

    async def allow(self) -> bool:
        """
        Check if operation is allowed (token available).

        Returns:
            True if allowed, False if rate limit exceeded
        """
        async with self.lock:
            now = time.time()

            # Refill tokens based on time elapsed
            elapsed = now - self.last_update
            self.tokens = min(self.max_frequency, self.tokens + elapsed * self.max_frequency)
            self.last_update = now

            # Check if token available
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return True

            return False
