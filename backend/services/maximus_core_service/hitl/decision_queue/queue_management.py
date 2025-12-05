"""
Queue Management Mixin for Decision Queue.

Handles enqueue/dequeue operations and queue access.
"""

from __future__ import annotations

import logging
from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..base_pkg import HITLDecision, RiskLevel
    from .models import QueuedDecision


class QueueManagementMixin:
    """
    Mixin for queue management operations.

    Handles adding, removing, and accessing decisions in the queue.
    """

    def enqueue(self, decision: HITLDecision) -> QueuedDecision:
        """
        Add decision to queue.

        Args:
            decision: Decision to enqueue

        Returns:
            QueuedDecision wrapper

        Raises:
            ValueError: If queue is full
        """
        # Check queue size
        if self.max_size > 0 and self.get_total_size() >= self.max_size:
            raise ValueError(f"Queue is full (max_size={self.max_size})")

        # Create queued decision
        from .models import QueuedDecision

        queued = QueuedDecision(
            decision=decision,
            priority_score=self._calculate_priority(decision),
        )

        # Add to appropriate queue
        risk_queue = self._queues[decision.risk_level]
        risk_queue.append(queued)

        # Add to lookup
        self._decisions[decision.decision_id] = queued

        # Update metrics
        self.metrics["total_enqueued"] += 1

        self.logger.info(
            "Decision enqueued: %s (risk=%s, queue_size=%d)",
            decision.decision_id,
            decision.risk_level.value,
            len(risk_queue),
        )

        return queued

    def dequeue(
        self, risk_level: RiskLevel | None = None, operator_id: str | None = None
    ) -> HITLDecision | None:
        """
        Remove and return highest priority decision from queue.

        Args:
            risk_level: Specific risk level to dequeue from (None = highest priority)
            operator_id: Operator ID (for assignment tracking)

        Returns:
            HITLDecision, or None if queue is empty
        """
        from ..base_pkg import RiskLevel

        # Determine which queue to dequeue from
        if risk_level:
            queues_to_check = [risk_level]
        else:
            # Check in priority order: CRITICAL > HIGH > MEDIUM > LOW
            queues_to_check = [
                RiskLevel.CRITICAL,
                RiskLevel.HIGH,
                RiskLevel.MEDIUM,
                RiskLevel.LOW,
            ]

        # Find first non-empty queue
        for level in queues_to_check:
            queue = self._queues[level]
            if queue:
                queued = queue.popleft()
                decision = queued.decision

                # Remove from lookup
                del self._decisions[decision.decision_id]

                # Assign to operator if provided
                if operator_id:
                    self._assign_to_operator(decision, operator_id)

                # Update metrics
                self.metrics["total_dequeued"] += 1

                self.logger.info(
                    "Decision dequeued: %s (risk=%s, operator=%s)",
                    decision.decision_id,
                    decision.risk_level.value,
                    operator_id,
                )

                return decision

        return None  # All queues empty

    def get_pending_decisions(
        self, risk_level: RiskLevel | None = None, operator_id: str | None = None
    ) -> list[HITLDecision]:
        """
        Get pending decisions without removing from queue.

        Args:
            risk_level: Filter by risk level (None = all)
            operator_id: Filter by assigned operator (None = all)

        Returns:
            List of pending decisions
        """
        decisions = []

        # Determine which queues to check
        if risk_level:
            queues_to_check = [(risk_level, self._queues[risk_level])]
        else:
            queues_to_check = list(self._queues.items())

        # Collect decisions
        for level, queue in queues_to_check:
            for queued in queue:
                # Filter by operator if specified
                # Only skip if decision is assigned to a DIFFERENT operator
                # Unassigned decisions (None) are available to all operators
                if (
                    operator_id
                    and queued.decision.assigned_operator is not None
                    and queued.decision.assigned_operator != operator_id
                ):
                    continue

                decisions.append(queued.decision)

        return decisions

    def get_decision(self, decision_id: str) -> QueuedDecision | None:
        """Get decision from queue by ID (without removing)."""
        return self._decisions.get(decision_id)

    def remove_decision(self, decision_id: str) -> bool:
        """
        Remove decision from queue by ID.

        Args:
            decision_id: Decision ID to remove

        Returns:
            True if removed, False if not found
        """
        queued = self._decisions.get(decision_id)
        if queued is None:
            return False

        # Remove from queue
        risk_level = queued.decision.risk_level
        queue = self._queues[risk_level]

        try:
            queue.remove(queued)
            del self._decisions[decision_id]
            self.logger.info("Decision removed from queue: %s", decision_id)
            return True
        except ValueError:
            self.logger.warning("Decision not in queue: %s", decision_id)
            return False
