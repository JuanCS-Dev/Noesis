"""
Review Queueing Mixin for Decision Framework.

Handles queuing decisions for human review.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .models import DecisionResult

if TYPE_CHECKING:
    from ..base_pkg import HITLDecision


class ReviewQueueingMixin:
    """
    Mixin for queuing decisions for human review.

    Integrates with DecisionQueue to manage review workflow.
    """

    def _queue_for_review(self, decision: HITLDecision) -> DecisionResult:
        """
        Queue decision for human review.

        Args:
            decision: Decision to queue

        Returns:
            DecisionResult with queued status
        """
        if self._decision_queue is None:
            self.logger.warning("Decision queue not set - decision will not be queued")
            return DecisionResult(decision=decision, queued=False)

        # Add to queue
        queued_decision = self._decision_queue.enqueue(decision)

        # Log to audit trail
        if self._audit_trail:
            audit_entry = self._audit_trail.log_decision_queued(decision, queued_decision.queue_priority)
            audit_entry_id = audit_entry.entry_id
        else:
            audit_entry_id = None

        result = DecisionResult(
            decision=decision,
            queued=True,
            audit_entry_id=audit_entry_id,
        )

        self.logger.info(
            "Decision queued: %s (automation_level=%s, sla_deadline=%s)",
            decision.decision_id,
            decision.automation_level.value,
            decision.sla_deadline,
        )

        return result
