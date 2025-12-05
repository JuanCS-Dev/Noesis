"""
Operator Integration Mixin for Decision Framework.

Handles operator actions (reject, escalate).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from ..base_pkg import DecisionStatus

if TYPE_CHECKING:
    from ..base_pkg import HITLDecision, OperatorAction


class OperatorIntegrationMixin:
    """
    Mixin for operator decision handling.

    Provides reject and escalate operations.
    """

    def reject_decision(self, decision: HITLDecision, operator_action: OperatorAction) -> None:
        """
        Reject a decision (operator veto).

        Args:
            decision: Decision to reject
            operator_action: Operator action with rejection reasoning
        """
        self.logger.info("Decision rejected: %s by %s", decision.decision_id, operator_action.operator_id)

        decision.status = DecisionStatus.REJECTED
        decision.reviewed_by = operator_action.operator_id
        decision.reviewed_at = datetime.utcnow()
        decision.operator_comment = operator_action.comment

        self.metrics["rejected"] += 1

        # Log to audit trail
        if self._audit_trail:
            self._audit_trail.log_decision_rejected(decision, operator_action)

    def escalate_decision(
        self, decision: HITLDecision, escalation_reason: str, escalated_to: str
    ) -> None:
        """
        Escalate decision to higher authority.

        Args:
            decision: Decision to escalate
            escalation_reason: Reason for escalation
            escalated_to: Target role/person
        """
        self.logger.info(
            "Decision escalated: %s → %s (reason: %s)",
            decision.decision_id,
            escalated_to,
            escalation_reason,
        )

        decision.status = DecisionStatus.ESCALATED
        decision.escalated = True
        decision.escalated_to = escalated_to
        decision.escalated_at = datetime.utcnow()
        decision.escalation_reason = escalation_reason

        self.metrics["escalated"] += 1

        # Log to audit trail
        if self._audit_trail:
            self._audit_trail.log_decision_escalated(decision, escalation_reason, escalated_to)
