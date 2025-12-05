"""
Core Decision Queue Implementation.

Main decision queue combining all mixins.
"""

from __future__ import annotations

import logging
from collections import deque

from ..base_pkg import RiskLevel, SLAConfig
from .metrics import MetricsMixin
from .operator_assignment import OperatorAssignmentMixin
from .priority import PriorityMixin
from .queue_management import QueueManagementMixin
from .sla_callbacks import SLACallbacksMixin
from .sla_monitor import SLAMonitor


class DecisionQueue(
    QueueManagementMixin,
    OperatorAssignmentMixin,
    PriorityMixin,
    MetricsMixin,
    SLACallbacksMixin,
):
    """
    Priority queue for decisions awaiting human review.

    Implements multi-level priority queue with SLA monitoring.

    Inherits from:
        - QueueManagementMixin: enqueue, dequeue, get_pending_decisions
        - OperatorAssignmentMixin: assign_to_operator, get_next_operator_round_robin
        - PriorityMixin: _calculate_priority
        - MetricsMixin: get_total_size, get_size_by_risk, get_metrics
        - SLACallbacksMixin: check_sla_status, _handle_sla_warning, _handle_sla_violation
    """

    def __init__(self, sla_config: SLAConfig | None = None, max_size: int = 1000) -> None:
        """
        Initialize decision queue.

        Args:
            sla_config: SLA configuration
            max_size: Maximum queue size (0 = unlimited)
        """
        self.sla_config = sla_config or SLAConfig()
        self.max_size = max_size
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Priority queues (one per risk level)
        self._queues: dict[RiskLevel, deque] = {
            RiskLevel.CRITICAL: deque(),
            RiskLevel.HIGH: deque(),
            RiskLevel.MEDIUM: deque(),
            RiskLevel.LOW: deque(),
        }

        # Decision lookup (by decision_id)
        from .models import QueuedDecision

        self._decisions: dict[str, QueuedDecision] = {}

        # Operator assignment tracking
        self._operators: set[str] = set()
        self._operator_assignments: dict[str, list[str]] = {}  # operator_id -> [decision_ids]
        self._current_operator_index: int = 0  # For round-robin

        # SLA monitor
        self.sla_monitor = SLAMonitor(self.sla_config)
        self.sla_monitor.register_warning_callback(self._handle_sla_warning)
        self.sla_monitor.register_violation_callback(self._handle_sla_violation)
        self.sla_monitor.start()

        # Metrics
        self.metrics = {
            "total_enqueued": 0,
            "total_dequeued": 0,
            "total_assigned": 0,
            "sla_warnings": 0,
            "sla_violations": 0,
        }

        self.logger.info("Decision Queue initialized")

    def __del__(self) -> None:
        """Cleanup: stop SLA monitor."""
        if hasattr(self, "sla_monitor"):
            self.sla_monitor.stop()
