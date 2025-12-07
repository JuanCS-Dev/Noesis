"""Operator Action Methods.

Mixin providing decision action methods.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from ..base_pkg import OperatorAction

if TYPE_CHECKING:
    from ..base_pkg import HITLDecision
    from .interface import OperatorInterface
    from .models import OperatorSession

logger = logging.getLogger(__name__)


class ActionMixin:
    """Mixin providing decision action methods.

    Provides methods for:
    - Approving decisions
    - Rejecting decisions
    - Modifying and approving decisions
    - Escalating decisions
    """

    def approve_decision(
        self: OperatorInterface,
        session_id: str,
        decision_id: str,
        comment: str = "",
    ) -> dict[str, Any]:
        """Approve and execute decision.

        Args:
            session_id: Operator session ID.
            decision_id: Decision ID to approve.
            comment: Optional operator comment.

        Returns:
            Result dict with execution details.
        """
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"Invalid or expired session: {session_id}")

        session.update_activity()

        decision = self._get_decision(decision_id)
        if decision is None:
            raise ValueError(f"Decision not found: {decision_id}")

        operator_action = OperatorAction(
            decision_id=decision_id,
            operator_id=session.operator_id,
            action="approve",
            comment=comment,
            session_id=session_id,
            ip_address=session.ip_address,
        )

        if self.decision_framework is None:
            raise RuntimeError("Decision framework not set")

        result = self.decision_framework.execute_decision(decision, operator_action)

        session.decisions_reviewed += 1
        session.decisions_approved += 1

        if self.decision_queue:
            self.decision_queue.remove_decision(decision_id)

        logger.info(
            "Decision approved: %s by %s (executed=%s)",
            decision_id,
            session.operator_id,
            result.executed,
        )

        return {
            "decision_id": decision_id,
            "status": "approved",
            "executed": result.executed,
            "result": result.execution_output,
            "error": result.execution_error,
        }

    def reject_decision(
        self: OperatorInterface,
        session_id: str,
        decision_id: str,
        reason: str,
        comment: str = "",
    ) -> dict[str, Any]:
        """Reject decision (veto AI recommendation).

        Args:
            session_id: Operator session ID.
            decision_id: Decision ID to reject.
            reason: Rejection reason (required).
            comment: Additional comments.

        Returns:
            Result dict.
        """
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"Invalid or expired session: {session_id}")

        session.update_activity()

        decision = self._get_decision(decision_id)
        if decision is None:
            raise ValueError(f"Decision not found: {decision_id}")

        operator_action = OperatorAction(
            decision_id=decision_id,
            operator_id=session.operator_id,
            action="reject",
            comment=comment,
            reasoning=reason,
            session_id=session_id,
            ip_address=session.ip_address,
        )

        if self.decision_framework is None:
            raise RuntimeError("Decision framework not set")

        self.decision_framework.reject_decision(decision, operator_action)

        rejection_count = decision.metadata.get("rejection_count", 0) + 1
        decision.metadata["rejection_count"] = rejection_count

        session.decisions_reviewed += 1
        session.decisions_rejected += 1

        if self.decision_queue:
            self.decision_queue.remove_decision(decision_id)

        logger.info(
            "Decision rejected: %s by %s (reason=%s)",
            decision_id,
            session.operator_id,
            reason,
        )

        return {
            "decision_id": decision_id,
            "status": "rejected",
            "reason": reason,
        }

    def modify_and_approve(
        self: OperatorInterface,
        session_id: str,
        decision_id: str,
        modifications: dict[str, Any],
        comment: str = "",
    ) -> dict[str, Any]:
        """Modify decision parameters and execute.

        Args:
            session_id: Operator session ID.
            decision_id: Decision ID.
            modifications: Parameter modifications.
            comment: Operator comment.

        Returns:
            Result dict with execution details.
        """
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"Invalid or expired session: {session_id}")

        session.update_activity()

        decision = self._get_decision(decision_id)
        if decision is None:
            raise ValueError(f"Decision not found: {decision_id}")

        operator_action = OperatorAction(
            decision_id=decision_id,
            operator_id=session.operator_id,
            action="modify",
            comment=comment,
            modifications=modifications,
            session_id=session_id,
            ip_address=session.ip_address,
        )

        if self.decision_framework is None:
            raise RuntimeError("Decision framework not set")

        result = self.decision_framework.execute_decision(decision, operator_action)

        session.decisions_reviewed += 1
        session.decisions_approved += 1
        session.decisions_modified += 1

        if self.decision_queue:
            self.decision_queue.remove_decision(decision_id)

        logger.info(
            "Decision modified and approved: %s by %s (modifications=%s)",
            decision_id,
            session.operator_id,
            modifications,
        )

        return {
            "decision_id": decision_id,
            "status": "modified_and_approved",
            "modifications": modifications,
            "executed": result.executed,
            "result": result.execution_output,
            "error": result.execution_error,
        }

    def escalate_decision(
        self: OperatorInterface,
        session_id: str,
        decision_id: str,
        reason: str,
        comment: str = "",
    ) -> dict[str, Any]:
        """Escalate decision to higher authority.

        Args:
            session_id: Operator session ID.
            decision_id: Decision ID to escalate.
            reason: Escalation reason.
            comment: Additional comments.

        Returns:
            Result dict with escalation details.
        """
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"Invalid or expired session: {session_id}")

        session.update_activity()

        decision = self._get_decision(decision_id)
        if decision is None:
            raise ValueError(f"Decision not found: {decision_id}")

        if self.escalation_manager is None:
            raise RuntimeError("Escalation manager not set")

        escalation_target = self.escalation_manager.get_escalation_target(
            session.operator_role, decision
        )

        from ..escalation_manager import EscalationType

        escalation_event = self.escalation_manager.escalate_decision(
            decision=decision,
            escalation_type=EscalationType.OPERATOR_REQUEST,
            reason=reason,
            target_role=escalation_target,
        )

        session.decisions_reviewed += 1
        session.decisions_escalated += 1

        logger.info(
            "Decision escalated: %s by %s -> %s",
            decision_id,
            session.operator_id,
            escalation_target,
        )

        return {
            "decision_id": decision_id,
            "status": "escalated",
            "escalated_to": escalation_target,
            "escalation_event_id": escalation_event.event_id,
            "reason": reason,
        }
