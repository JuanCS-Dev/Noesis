"""
SLA Callbacks Mixin for Decision Queue.

Handles SLA warning and violation callbacks from SLAMonitor.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..base_pkg import HITLDecision


class SLACallbacksMixin:
    """
    Mixin for SLA callback handling.

    Receives callbacks from SLAMonitor for warnings and violations.
    """

    def check_sla_status(self) -> None:
        """Check SLA status for all queued decisions."""
        for queued in self._decisions.values():
            self.sla_monitor.check_decision(queued)

    def _handle_sla_warning(self, decision: HITLDecision) -> None:
        """
        Handle SLA warning (callback from SLAMonitor).

        Args:
            decision: Decision with SLA warning
        """
        self.metrics["sla_warnings"] += 1
        self.logger.warning(
            "SLA warning for decision: %s (risk=%s)",
            decision.decision_id,
            decision.risk_level.value,
        )

    def _handle_sla_violation(self, decision: HITLDecision) -> None:
        """
        Handle SLA violation (callback from SLAMonitor).

        Args:
            decision: Decision with SLA violation
        """
        self.metrics["sla_violations"] += 1
        self.logger.error(
            "SLA violation for decision: %s (risk=%s)",
            decision.decision_id,
            decision.risk_level.value,
        )
