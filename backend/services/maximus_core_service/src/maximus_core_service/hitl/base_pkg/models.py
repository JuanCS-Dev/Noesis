"""Data models for HITL module."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .enums import ActionType, AutomationLevel, DecisionStatus, RiskLevel


@dataclass
class DecisionContext:
    """Context information for a HITL decision."""

    threat_id: str
    threat_type: str
    threat_severity: str
    affected_assets: list[str]
    indicators: dict[str, Any]
    confidence_score: float
    risk_level: RiskLevel
    recommended_action: ActionType
    automation_level: AutomationLevel
    justification: str
    additional_context: dict[str, Any] = field(default_factory=dict)


@dataclass
class HITLDecision:
    """Represents a Human-in-the-Loop decision request."""

    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    context: DecisionContext | None = None
    status: DecisionStatus = DecisionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    sla_deadline: datetime | None = None
    assigned_operator: str | None = None
    operator_decision: str | None = None
    operator_feedback: str | None = None
    execution_result: dict[str, Any] | None = None
    escalation_history: list[dict[str, Any]] = field(default_factory=list)

    def is_sla_violated(self) -> bool:
        """Check if SLA deadline has passed."""
        if self.sla_deadline is None:
            return False
        return datetime.utcnow() > self.sla_deadline

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "decision_id": self.decision_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "sla_deadline": self.sla_deadline.isoformat() if self.sla_deadline else None,
            "assigned_operator": self.assigned_operator,
            "operator_decision": self.operator_decision,
            "operator_feedback": self.operator_feedback,
        }


@dataclass
class OperatorAction:
    """Represents an operator's action on a decision."""

    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    decision_id: str = ""
    operator_id: str = ""
    action_type: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    feedback: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditEntry:
    """Audit log entry for HITL actions."""

    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    decision_id: str = ""
    event_type: str = ""
    actor: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entry_id": self.entry_id,
            "decision_id": self.decision_id,
            "event_type": self.event_type,
            "actor": self.actor,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
        }
