"""HITL Engine - Models and Configuration.

Pydantic models and enumerations for the HITL engine.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class AlertStatus(str, Enum):
    """Alert status states."""

    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    DISMISSED = "dismissed"


class AlertPriority(str, Enum):
    """Alert priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DecisionType(str, Enum):
    """Types of decisions that can be requested."""

    BLOCK_IP = "block_ip"
    ISOLATE_HOST = "isolate_host"
    QUARANTINE_FILE = "quarantine_file"
    TERMINATE_PROCESS = "terminate_process"
    REVOKE_ACCESS = "revoke_access"
    ESCALATE = "escalate"
    INVESTIGATE = "investigate"
    DISMISS = "dismiss"


class ApprovalStatus(str, Enum):
    """Approval status for decisions."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    EXECUTED = "executed"


class Alert(BaseModel):
    """Alert model."""

    alert_id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str
    source: str
    priority: AlertPriority
    status: AlertStatus = AlertStatus.PENDING
    threat_score: float = Field(ge=0.0, le=1.0)
    entities: Dict[str, Any] = Field(default_factory=dict)
    mitre_tactics: List[str] = Field(default_factory=list)
    mitre_techniques: List[str] = Field(default_factory=list)
    recommended_actions: List[DecisionType] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    assigned_to: Optional[str] = None
    notes: List[str] = Field(default_factory=list)
    related_alerts: List[str] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)


class DecisionRequest(BaseModel):
    """Decision request model."""

    request_id: str = Field(default_factory=lambda: str(uuid4()))
    alert_id: str
    decision_type: DecisionType
    target: Dict[str, Any]
    reason: str
    risk_level: str
    automated: bool = False
    requires_approval: bool = True
    approval_timeout_minutes: int = 30
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


class DecisionResponse(BaseModel):
    """Decision response model."""

    response_id: str = Field(default_factory=lambda: str(uuid4()))
    request_id: str
    alert_id: str
    decision_type: DecisionType
    status: ApprovalStatus
    approver: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLog(BaseModel):
    """Audit log entry."""

    log_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: str
    actor: str
    target: Dict[str, Any]
    result: str
    details: Dict[str, Any] = Field(default_factory=dict)


class WorkflowState(BaseModel):
    """Workflow state tracking."""

    workflow_id: str = Field(default_factory=lambda: str(uuid4()))
    alert_id: str
    current_stage: str
    stages_completed: List[str] = Field(default_factory=list)
    decisions_pending: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class HITLConfig(BaseModel):
    """HITL configuration."""

    alert_retention_days: int = 90
    max_pending_alerts: int = 1000
    escalation_threshold: float = 0.8
    auto_escalate_after_minutes: int = 60
    decision_timeout_minutes: int = 30
    require_dual_approval: bool = False
    audit_all_actions: bool = True
    alert_grouping_window_minutes: int = 15
    max_related_alerts: int = 10
