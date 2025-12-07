"""
Metrics Mixin for Decision Queue.

Handles queue metrics and statistics.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..base_pkg import RiskLevel


class MetricsMixin:
    """
    Mixin for queue metrics and statistics.

    Provides methods to retrieve queue size, metrics, and performance data.
    """

    def get_total_size(self) -> int:
        """
        Get total number of decisions in queue.

        Returns:
            Total queue size
        """
        return sum(len(queue) for queue in self._queues.values())

    def get_size_by_risk(self) -> dict[RiskLevel, int]:
        """
        Get queue size by risk level.

        Returns:
            Dictionary mapping risk level to queue size
        """
        return {level: len(queue) for level, queue in self._queues.items()}

    def get_metrics(self) -> dict[str, Any]:
        """
        Get queue metrics.

        Returns:
            Dictionary containing all queue metrics
        """
        return {
            **self.metrics,
            "current_queue_size": self.get_total_size(),
            "queue_by_risk": {level.value: size for level, size in self.get_size_by_risk().items()},
            "average_time_in_queue": self._calculate_average_time_in_queue(),
        }

    def _calculate_average_time_in_queue(self) -> float:
        """
        Calculate average time decisions spend in queue (seconds).

        Returns:
            Average queue time in seconds
        """
        if not self._decisions:
            return 0.0

        total_time = sum(queued.get_time_in_queue().total_seconds() for queued in self._decisions.values())
        return total_time / len(self._decisions)
