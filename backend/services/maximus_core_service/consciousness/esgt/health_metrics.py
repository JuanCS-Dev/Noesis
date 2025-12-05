"""Health Metrics Mixin - ESGT health monitoring and degraded mode management."""

from __future__ import annotations

import time
from typing import Any, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from .coordinator import ESGTCoordinator


class HealthMetricsMixin:
    """Mixin providing health metrics and degraded mode management for ESGT."""

    def get_success_rate(self: "ESGTCoordinator") -> float:
        """Get percentage of successful ESGT events."""
        if self.total_events == 0:
            return 0.0
        return self.successful_events / self.total_events

    def get_recent_coherence(self: "ESGTCoordinator", window: int = 10) -> float:
        """Get average coherence of recent events."""
        recent = self.event_history[-window:]
        if not recent:
            return 0.0

        coherences = [e.achieved_coherence for e in recent if e.success]
        return float(np.mean(coherences)) if coherences else 0.0

    def _enter_degraded_mode(self: "ESGTCoordinator") -> None:
        """Enter degraded mode - reduce ignition rate due to low coherence."""
        self.degraded_mode = True
        self.max_concurrent = 1
        logger.warning(
            "⚠️  ESGT: Entering DEGRADED MODE - "
            "reducing ignition rate due to low coherence"
        )

    def _exit_degraded_mode(self: "ESGTCoordinator") -> None:
        """Exit degraded mode - restore normal operation when coherence improves."""
        self.degraded_mode = False
        self.max_concurrent = self.MAX_CONCURRENT_EVENTS
        logger.info("✓ ESGT: Exiting DEGRADED MODE - coherence restored")

    def get_health_metrics(self: "ESGTCoordinator") -> dict[str, Any]:
        """Get ESGT health metrics for Safety Core integration."""
        # Compute current frequency
        now = time.time()
        recent_ignitions = [
            t for t in self.ignition_timestamps if now - t < 1.0
        ]  # Last second
        current_frequency = len(recent_ignitions)

        # Compute average coherence
        avg_coherence = (
            sum(self.coherence_history) / len(self.coherence_history)
            if self.coherence_history
            else 0.0
        )

        return {
            "frequency_hz": current_frequency,
            "active_events": len(self.active_events),
            "degraded_mode": self.degraded_mode,
            "average_coherence": avg_coherence,
            "circuit_breaker_state": self.ignition_breaker.state,
            "total_events": self.total_events,
            "successful_events": self.successful_events,
        }
