"""
Metrics and History Mixin.

Handles escalation metrics and history tracking.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .models import EscalationEvent


class MetricsHistoryMixin:
    """
    Mixin for metrics and history tracking.

    Provides methods to retrieve escalation metrics and history.
    """

    def get_metrics(self) -> dict[str, Any]:
        """
        Get escalation metrics.

        Returns:
            Dictionary containing escalation metrics
        """
        return {
            **self.metrics,
            "escalation_rate": (
                self.metrics["total_escalations"] / len(self.escalation_history)
                if self.escalation_history
                else 0.0
            ),
        }

    def get_escalation_history(
        self, decision_id: str | None = None, limit: int = 100
    ) -> list[EscalationEvent]:
        """
        Get escalation history.

        Args:
            decision_id: Filter by decision ID (optional)
            limit: Maximum number of events to return

        Returns:
            List of escalation events
        """
        if decision_id:
            events = [e for e in self.escalation_history if e.decision_id == decision_id]
        else:
            events = self.escalation_history

        # Return most recent first
        return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]
