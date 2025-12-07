"""
Governance Enums.

Defines types and severity levels for governance operations.
"""

from __future__ import annotations

from enum import Enum


class PolicyType(str, Enum):
    """Types of ethical policies."""

    ETHICAL_USE = "ethical_use"
    RED_TEAMING = "red_teaming"
    DATA_PRIVACY = "data_privacy"
    INCIDENT_RESPONSE = "incident_response"
    WHISTLEBLOWER = "whistleblower"


class PolicySeverity(str, Enum):
    """Severity levels for policy violations."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ERBMemberRole(str, Enum):
    """Roles for Ethics Review Board members."""

    CHAIR = "chair"
    VICE_CHAIR = "vice_chair"
    TECHNICAL_MEMBER = "technical_member"
    LEGAL_MEMBER = "legal_member"
    EXTERNAL_ADVISOR = "external_advisor"
    OBSERVER = "observer"


class DecisionType(str, Enum):
    """Types of ERB decisions."""

    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    CONDITIONAL_APPROVED = "conditional_approved"
    REQUIRES_REVISION = "requires_revision"


class AuditLogLevel(str, Enum):
    """Audit log levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class GovernanceAction(str, Enum):
    """Governance-related actions for audit trail."""

    POLICY_CREATED = "policy_created"
    POLICY_UPDATED = "policy_updated"
    POLICY_VIOLATED = "policy_violated"
    ERB_MEETING_SCHEDULED = "erb_meeting_scheduled"
    ERB_DECISION_MADE = "erb_decision_made"
    ERB_MEMBER_ADDED = "erb_member_added"
    ERB_MEMBER_REMOVED = "erb_member_removed"
    AUDIT_LOG_CREATED = "audit_log_created"
    INCIDENT_REPORTED = "incident_reported"
    WHISTLEBLOWER_REPORT = "whistleblower_report"
