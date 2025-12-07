"""
Governance API Request/Response Models.

Pydantic models for Governance HITL API.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    """Request to create operator session."""

    operator_id: str = Field(..., description="Unique operator identifier")
    operator_name: str = Field(..., description="Operator display name")
    operator_role: str = Field(default="soc_operator", description="Operator role")
    ip_address: str | None = Field(None, description="Client IP address")
    user_agent: str | None = Field(None, description="Client user agent")


class SessionCreateResponse(BaseModel):
    """Response from session creation."""

    session_id: str
    operator_id: str
    expires_at: str
    message: str = "Session created successfully"


class DecisionActionRequest(BaseModel):
    """Request to act on a decision."""

    session_id: str = Field(..., description="Active session ID")
    reasoning: str | None = Field(None, description="Reasoning for action")
    comment: str | None = Field(None, description="Additional comments")


class ApproveDecisionRequest(DecisionActionRequest):
    """Request to approve a decision.

    Inherits all fields from DecisionActionRequest:
    - session_id: Operator session identifier
    - comment: Optional approval comments
    """

    ...


class RejectDecisionRequest(DecisionActionRequest):
    """Request to reject a decision."""

    reason: str = Field(..., description="Rejection reason (required)")


class EscalateDecisionRequest(DecisionActionRequest):
    """Request to escalate a decision."""

    escalation_target: str | None = Field(None, description="Target role/person")
    escalation_reason: str = Field(..., description="Why escalation is needed")


class DecisionActionResponse(BaseModel):
    """Response from decision action."""

    decision_id: str
    action: str  # "approved", "rejected", "escalated"
    status: str
    message: str
    executed: bool | None = None
    result: dict | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    active_connections: int
    total_connections: int
    decisions_streamed: int
    queue_size: int
    timestamp: str


class PendingStatsResponse(BaseModel):
    """Pending decisions statistics."""

    total_pending: int
    by_risk_level: dict[str, int]
    oldest_pending_seconds: int | None
    sla_violations: int


class DecisionResponse(BaseModel):
    """Individual decision response."""

    decision_id: str
    status: str
    risk_level: str
    automation_level: str
    created_at: str
    sla_deadline: str | None
    context: dict
    resolution: dict | None = None


class OperatorStatsResponse(BaseModel):
    """Operator statistics."""

    operator_id: str
    total_sessions: int
    total_decisions_reviewed: int
    total_approved: int
    total_rejected: int
    total_escalated: int
    approval_rate: float
    rejection_rate: float
    escalation_rate: float
    average_review_time: float
