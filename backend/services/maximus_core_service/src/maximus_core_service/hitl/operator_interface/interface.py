"""Operator Interface.

Interface for SOC operators to review and act on HITL decisions.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from ..base_pkg import HITLDecision, RiskLevel
from .actions import ActionMixin
from .models import OperatorMetrics, OperatorSession

logger = logging.getLogger(__name__)


class OperatorInterface(ActionMixin):
    """Interface for SOC operators to review and act on HITL decisions.

    Provides methods for decision review, approval, rejection, modification,
    and escalation.

    Attributes:
        decision_framework: HITLDecisionFramework instance.
        decision_queue: DecisionQueue instance.
        escalation_manager: EscalationManager instance.
        audit_trail: AuditTrail instance.
        session_timeout: Session timeout duration.
    """

    def __init__(
        self,
        decision_framework: Any = None,
        decision_queue: Any = None,
        escalation_manager: Any = None,
        audit_trail: Any = None,
    ) -> None:
        """Initialize operator interface.

        Args:
            decision_framework: HITLDecisionFramework instance.
            decision_queue: DecisionQueue instance.
            escalation_manager: EscalationManager instance.
            audit_trail: AuditTrail instance.
        """
        self.decision_framework = decision_framework
        self.decision_queue = decision_queue
        self.escalation_manager = escalation_manager
        self.audit_trail = audit_trail

        self._sessions: dict[str, OperatorSession] = {}
        self._operator_metrics: dict[str, OperatorMetrics] = {}
        self.session_timeout = timedelta(hours=8)

        logger.info("Operator Interface initialized")

    def create_session(
        self,
        operator_id: str,
        operator_name: str,
        operator_role: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> OperatorSession:
        """Create new operator session.

        Args:
            operator_id: Unique operator identifier.
            operator_name: Operator display name.
            operator_role: Operator role.
            ip_address: Client IP address.
            user_agent: Client user agent.

        Returns:
            New operator session.
        """
        session_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + self.session_timeout

        session = OperatorSession(
            session_id=session_id,
            operator_id=operator_id,
            operator_name=operator_name,
            operator_role=operator_role,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self._sessions[session_id] = session

        if operator_id not in self._operator_metrics:
            self._operator_metrics[operator_id] = OperatorMetrics(
                operator_id=operator_id
            )

        logger.info(
            "Session created: %s (operator=%s, role=%s)",
            session_id,
            operator_id,
            operator_role,
        )

        return session

    def get_session(self, session_id: str) -> OperatorSession | None:
        """Get active session by ID.

        Args:
            session_id: Session identifier.

        Returns:
            Session if found and not expired, None otherwise.
        """
        session = self._sessions.get(session_id)
        if session and session.is_expired():
            self._close_session(session_id)
            return None
        return session

    def _close_session(self, session_id: str) -> None:
        """Close session and update metrics.

        Args:
            session_id: Session identifier.
        """
        session = self._sessions.get(session_id)
        if session:
            metrics = self._operator_metrics.get(session.operator_id)
            if metrics:
                metrics.update_from_session(session)

            del self._sessions[session_id]

            logger.info(
                "Session closed: %s (duration=%s, decisions_reviewed=%d)",
                session_id,
                session.get_session_duration(),
                session.decisions_reviewed,
            )

    def get_pending_decisions(
        self,
        session_id: str,
        risk_level: RiskLevel | None = None,
        limit: int = 20,
    ) -> list[HITLDecision]:
        """Get pending decisions for operator review.

        Args:
            session_id: Operator session ID.
            risk_level: Filter by risk level.
            limit: Maximum number to return.

        Returns:
            List of pending decisions.
        """
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"Invalid or expired session: {session_id}")

        session.update_activity()

        if self.decision_queue is None:
            logger.warning("Decision queue not set")
            return []

        decisions = self.decision_queue.get_pending_decisions(
            risk_level=risk_level, operator_id=session.operator_id
        )

        decisions.sort(
            key=lambda d: (
                4 - list(RiskLevel).index(d.risk_level),
                d.sla_deadline or datetime.max,
            )
        )

        return decisions[:limit]

    def get_operator_metrics(self, operator_id: str) -> OperatorMetrics | None:
        """Get metrics for operator.

        Args:
            operator_id: Operator identifier.

        Returns:
            Operator metrics or None if not found.
        """
        return self._operator_metrics.get(operator_id)

    def get_session_metrics(self, session_id: str) -> dict[str, Any] | None:
        """Get metrics for active session.

        Args:
            session_id: Session identifier.

        Returns:
            Session metrics dict or None if not found.
        """
        session = self.get_session(session_id)
        if session is None:
            return None

        return {
            "session_id": session.session_id,
            "operator_id": session.operator_id,
            "operator_name": session.operator_name,
            "operator_role": session.operator_role,
            "session_duration": session.get_session_duration().total_seconds(),
            "decisions_reviewed": session.decisions_reviewed,
            "decisions_approved": session.decisions_approved,
            "decisions_rejected": session.decisions_rejected,
            "decisions_escalated": session.decisions_escalated,
            "decisions_modified": session.decisions_modified,
            "approval_rate": session.get_approval_rate(),
            "rejection_rate": session.get_rejection_rate(),
        }

    def _get_decision(self, decision_id: str) -> HITLDecision | None:
        """Get decision from queue.

        Args:
            decision_id: Decision identifier.

        Returns:
            Decision or None if not found.
        """
        if self.decision_queue is None:
            return None

        queued = self.decision_queue.get_decision(decision_id)
        if queued:
            return queued.decision
        return None
