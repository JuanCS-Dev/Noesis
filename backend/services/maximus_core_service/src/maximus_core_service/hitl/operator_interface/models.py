"""Operator Interface Models.

Data models for operator sessions and metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


@dataclass
class OperatorSession:
    """Active operator session for decision review.

    Attributes:
        session_id: Unique session identifier.
        operator_id: Operator identifier.
        operator_name: Display name.
        operator_role: Role (soc_operator, soc_supervisor, etc.).
        started_at: Session start time.
        last_activity: Last activity timestamp.
        expires_at: Session expiration time.
        decisions_reviewed: Total decisions reviewed.
        decisions_approved: Approved decisions count.
        decisions_rejected: Rejected decisions count.
        decisions_escalated: Escalated decisions count.
        decisions_modified: Modified decisions count.
        active_decision_ids: Currently active decision IDs.
        ip_address: Client IP address.
        user_agent: Client user agent.
        metadata: Additional session metadata.
    """

    session_id: str
    operator_id: str
    operator_name: str
    operator_role: str

    started_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None

    decisions_reviewed: int = 0
    decisions_approved: int = 0
    decisions_rejected: int = 0
    decisions_escalated: int = 0
    decisions_modified: int = 0

    active_decision_ids: list[str] = field(default_factory=list)

    ip_address: str | None = None
    user_agent: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if session has expired.

        Returns:
            True if session is expired.
        """
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def get_session_duration(self) -> timedelta:
        """Get session duration.

        Returns:
            Duration since session start.
        """
        return datetime.utcnow() - self.started_at

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def get_approval_rate(self) -> float:
        """Get approval rate.

        Returns:
            Approval rate (0.0 to 1.0).
        """
        if self.decisions_reviewed == 0:
            return 0.0
        return self.decisions_approved / self.decisions_reviewed

    def get_rejection_rate(self) -> float:
        """Get rejection rate.

        Returns:
            Rejection rate (0.0 to 1.0).
        """
        if self.decisions_reviewed == 0:
            return 0.0
        return self.decisions_rejected / self.decisions_reviewed


@dataclass
class OperatorMetrics:
    """Aggregate metrics for an operator.

    Attributes:
        operator_id: Operator identifier.
        total_sessions: Total session count.
        total_decisions_reviewed: Total decisions reviewed.
        total_approved: Total approved decisions.
        total_rejected: Total rejected decisions.
        total_escalated: Total escalated decisions.
        total_modified: Total modified decisions.
        average_review_time: Average review time in seconds.
        total_session_time: Total session time in seconds.
        approval_rate: Overall approval rate.
        rejection_rate: Overall rejection rate.
        escalation_rate: Overall escalation rate.
        critical_decisions_handled: Critical decisions handled.
        high_risk_decisions_handled: High risk decisions handled.
    """

    operator_id: str

    total_sessions: int = 0
    total_decisions_reviewed: int = 0
    total_approved: int = 0
    total_rejected: int = 0
    total_escalated: int = 0
    total_modified: int = 0

    average_review_time: float = 0.0
    total_session_time: float = 0.0

    approval_rate: float = 0.0
    rejection_rate: float = 0.0
    escalation_rate: float = 0.0

    critical_decisions_handled: int = 0
    high_risk_decisions_handled: int = 0

    def update_from_session(self, session: OperatorSession) -> None:
        """Update metrics from completed session.

        Args:
            session: Completed operator session.
        """
        self.total_sessions += 1
        self.total_decisions_reviewed += session.decisions_reviewed
        self.total_approved += session.decisions_approved
        self.total_rejected += session.decisions_rejected
        self.total_escalated += session.decisions_escalated
        self.total_modified += session.decisions_modified

        self.total_session_time += session.get_session_duration().total_seconds()

        if self.total_decisions_reviewed > 0:
            self.approval_rate = self.total_approved / self.total_decisions_reviewed
            self.rejection_rate = self.total_rejected / self.total_decisions_reviewed
            self.escalation_rate = self.total_escalated / self.total_decisions_reviewed
