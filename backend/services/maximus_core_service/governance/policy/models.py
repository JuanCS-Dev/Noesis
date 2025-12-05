"""
Policy Data Models.

Contains policy, violation, and enforcement result models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from ..enums import PolicySeverity, PolicyType


@dataclass
class Policy:
    """Ethical policy definition."""

    policy_id: str = field(default_factory=lambda: str(uuid4()))
    policy_type: PolicyType = PolicyType.ETHICAL_USE
    version: str = "1.0"
    title: str = ""
    description: str = ""
    rules: list[str] = field(default_factory=list)
    scope: str = "all"  # all, maximus, immunis, rte, specific_service
    enforcement_level: PolicySeverity = PolicySeverity.MEDIUM
    auto_enforce: bool = True
    created_date: datetime = field(default_factory=datetime.utcnow)
    last_review_date: datetime | None = None
    next_review_date: datetime | None = None
    approved_by_erb: bool = False
    erb_decision_id: str | None = None
    stakeholders: list[str] = field(default_factory=list)  # Affected teams/systems
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_due_for_review(self) -> bool:
        """Check if policy is due for review."""
        if self.next_review_date is None:
            return False
        return datetime.utcnow() >= self.next_review_date

    def days_until_review(self) -> int:
        """Calculate days until next review."""
        if self.next_review_date is None:
            return -1
        delta = self.next_review_date - datetime.utcnow()
        return max(0, delta.days)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "policy_id": self.policy_id,
            "policy_type": self.policy_type.value,
            "version": self.version,
            "title": self.title,
            "description": self.description,
            "rules": self.rules,
            "scope": self.scope,
            "enforcement_level": self.enforcement_level.value,
            "auto_enforce": self.auto_enforce,
            "created_date": self.created_date.isoformat(),
            "last_review_date": self.last_review_date.isoformat() if self.last_review_date else None,
            "next_review_date": self.next_review_date.isoformat() if self.next_review_date else None,
            "approved_by_erb": self.approved_by_erb,
            "erb_decision_id": self.erb_decision_id,
            "stakeholders": self.stakeholders,
            "is_due_for_review": self.is_due_for_review(),
            "days_until_review": self.days_until_review(),
            "metadata": self.metadata,
        }


@dataclass
class PolicyViolation:
    """Policy violation record."""

    violation_id: str = field(default_factory=lambda: str(uuid4()))
    policy_id: str = ""
    policy_type: PolicyType = PolicyType.ETHICAL_USE
    severity: PolicySeverity = PolicySeverity.MEDIUM
    title: str = ""
    description: str = ""
    violated_rule: str = ""
    detection_method: str = "automated"  # automated, manual, whistleblower
    detected_by: str = "system"  # system, user_id, or "anonymous"
    detected_date: datetime = field(default_factory=datetime.utcnow)
    affected_system: str = ""  # maximus, immunis, rte, or specific service
    affected_users: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    remediation_required: bool = True
    remediation_status: str = "pending"  # pending, in_progress, completed, dismissed
    remediation_deadline: datetime | None = None
    assigned_to: str | None = None  # User responsible for remediation
    resolution_notes: str = ""
    resolved_date: datetime | None = None
    escalated_to_erb: bool = False
    erb_decision_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_overdue(self) -> bool:
        """Check if remediation is overdue."""
        if self.remediation_deadline is None or self.remediation_status == "completed":
            return False
        return datetime.utcnow() > self.remediation_deadline

    def days_until_deadline(self) -> int:
        """Calculate days until remediation deadline."""
        if self.remediation_deadline is None:
            return -1
        delta = self.remediation_deadline - datetime.utcnow()
        return delta.days

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "violation_id": self.violation_id,
            "policy_id": self.policy_id,
            "policy_type": self.policy_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "violated_rule": self.violated_rule,
            "detection_method": self.detection_method,
            "detected_by": self.detected_by,
            "detected_date": self.detected_date.isoformat(),
            "affected_system": self.affected_system,
            "affected_users": self.affected_users,
            "context": self.context,
            "remediation_required": self.remediation_required,
            "remediation_status": self.remediation_status,
            "remediation_deadline": self.remediation_deadline.isoformat() if self.remediation_deadline else None,
            "assigned_to": self.assigned_to,
            "resolution_notes": self.resolution_notes,
            "resolved_date": self.resolved_date.isoformat() if self.resolved_date else None,
            "escalated_to_erb": self.escalated_to_erb,
            "erb_decision_id": self.erb_decision_id,
            "is_overdue": self.is_overdue(),
            "days_until_deadline": self.days_until_deadline(),
            "metadata": self.metadata,
        }


@dataclass
class PolicyEnforcementResult:
    """Result of policy enforcement check."""

    is_compliant: bool = True
    policy_id: str = ""
    policy_type: PolicyType = PolicyType.ETHICAL_USE
    checked_rules: int = 0
    passed_rules: int = 0
    failed_rules: int = 0
    violations: list[PolicyViolation] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def compliance_percentage(self) -> float:
        """Calculate compliance percentage."""
        if self.checked_rules == 0:
            return 100.0
        return (self.passed_rules / self.checked_rules) * 100.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_compliant": self.is_compliant,
            "policy_id": self.policy_id,
            "policy_type": self.policy_type.value,
            "checked_rules": self.checked_rules,
            "passed_rules": self.passed_rules,
            "failed_rules": self.failed_rules,
            "violations": [v.to_dict() for v in self.violations],
            "warnings": self.warnings,
            "compliance_percentage": self.compliance_percentage(),
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }
