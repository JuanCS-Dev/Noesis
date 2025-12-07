"""
SLA Monitoring for Decision Queue.

Monitors decisions for SLA violations and warnings.
"""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

from ..base_pkg import DecisionStatus

if TYPE_CHECKING:
    from ..base_pkg import SLAConfig
    from .models import QueuedDecision


class SLAMonitor:
    """
    Monitors decisions for SLA violations and warnings.

    Runs periodic checks and triggers callbacks for:
    - SLA warnings (75% of time elapsed)
    - SLA violations (deadline exceeded)
    """

    def __init__(self, sla_config: SLAConfig, check_interval: int = 30) -> None:
        """
        Initialize SLA monitor.

        Args:
            sla_config: SLA configuration
            check_interval: Check interval in seconds
        """
        self.sla_config = sla_config
        self.check_interval = check_interval
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Callbacks
        self._warning_callbacks: list = []
        self._violation_callbacks: list = []

        # Monitoring state
        self._running = False
        self._monitor_thread: threading.Thread | None = None

        # Metrics
        self.metrics = {
            "warnings_sent": 0,
            "violations_detected": 0,
        }

    def register_warning_callback(self, callback) -> None:
        """Register callback for SLA warnings. Signature: callback(decision)"""
        self._warning_callbacks.append(callback)

    def register_violation_callback(self, callback) -> None:
        """Register callback for SLA violations. Signature: callback(decision)"""
        self._violation_callbacks.append(callback)

    def start(self) -> None:
        """Start SLA monitoring (in background thread)."""
        if self._running:
            self.logger.warning("SLA monitor already running")
            return

        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        self.logger.info("SLA monitor started (check_interval=%ds)", self.check_interval)

    def stop(self) -> None:
        """Stop SLA monitoring."""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        self.logger.info("SLA monitor stopped")

    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        import time

        while self._running:
            time.sleep(self.check_interval)

    def check_decision(self, queued_decision: QueuedDecision) -> None:
        """
        Check decision for SLA warning/violation.

        Args:
            queued_decision: Queued decision to check
        """
        # Check for warning
        if queued_decision.should_send_sla_warning(self.sla_config.warning_threshold):
            self._trigger_warning(queued_decision)

        # Check for violation
        if queued_decision.is_sla_violated():
            self._trigger_violation(queued_decision)

    def _trigger_warning(self, queued_decision: QueuedDecision) -> None:
        """Trigger SLA warning callbacks."""
        queued_decision.sla_warning_sent = True
        queued_decision.decision.sla_warning_sent = True
        self.metrics["warnings_sent"] += 1

        self.logger.warning(
            "SLA warning: %s (risk=%s, time_remaining=%s)",
            queued_decision.decision.decision_id,
            queued_decision.decision.risk_level.value,
            queued_decision.get_time_until_sla(),
        )

        for callback in self._warning_callbacks:
            try:
                callback(queued_decision.decision)
            except Exception as e:
                self.logger.error("SLA warning callback failed: %s", e, exc_info=True)

    def _trigger_violation(self, queued_decision: QueuedDecision) -> None:
        """Trigger SLA violation callbacks."""
        if queued_decision.sla_violated:
            return  # Already handled

        queued_decision.sla_violated = True
        queued_decision.decision.status = DecisionStatus.TIMEOUT
        self.metrics["violations_detected"] += 1

        self.logger.error(
            "SLA VIOLATION: %s (risk=%s, overdue_by=%s)",
            queued_decision.decision.decision_id,
            queued_decision.decision.risk_level.value,
            abs(queued_decision.get_time_until_sla()),
        )

        for callback in self._violation_callbacks:
            try:
                callback(queued_decision.decision)
            except Exception as e:
                self.logger.error("SLA violation callback failed: %s", e, exc_info=True)
