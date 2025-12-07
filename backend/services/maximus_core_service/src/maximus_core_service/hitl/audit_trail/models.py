"""
Audit Trail Data Models.

Contains data models for audit queries and compliance reports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..base_pkg import (
    AuditEntry,
    AutomationLevel,
    DecisionStatus,
    RiskLevel,
)


@dataclass
class AuditQuery:
    """
    Query parameters for audit trail search.
    """

    # Time range
    start_time: datetime | None = None
    end_time: datetime | None = None

    # Decision filters
    decision_ids: list[str] = field(default_factory=list)
    risk_levels: list[RiskLevel] = field(default_factory=list)
    automation_levels: list[AutomationLevel] = field(default_factory=list)
    statuses: list[DecisionStatus] = field(default_factory=list)

    # Actor filters
    operator_ids: list[str] = field(default_factory=list)
    actor_types: list[str] = field(default_factory=list)  # "ai", "human"

    # Event filters
    event_types: list[str] = field(default_factory=list)

    # Compliance filters
    compliance_tags: list[str] = field(default_factory=list)

    # Pagination
    limit: int = 100
    offset: int = 0

    # Sorting
    sort_by: str = "timestamp"  # "timestamp", "risk_level", "decision_id"
    sort_order: str = "desc"  # "asc", "desc"


@dataclass
class ComplianceReport:
    """
    Compliance report for regulatory requirements.
    """

    # Report details
    report_id: str
    generated_at: datetime = field(default_factory=datetime.utcnow)
    report_type: str = "hitl_compliance"

    # Time period
    period_start: datetime = field(default_factory=datetime.utcnow)
    period_end: datetime = field(default_factory=datetime.utcnow)

    # Summary statistics
    total_decisions: int = 0
    auto_executed: int = 0
    human_reviewed: int = 0
    approved: int = 0
    rejected: int = 0
    escalated: int = 0
    sla_violations: int = 0

    # Risk breakdown
    critical_decisions: int = 0
    high_risk_decisions: int = 0
    medium_risk_decisions: int = 0
    low_risk_decisions: int = 0

    # Operator statistics
    unique_operators: int = 0
    average_review_time: float = 0.0  # seconds

    # Compliance metrics
    automation_rate: float = 0.0
    human_oversight_rate: float = 0.0
    sla_compliance_rate: float = 0.0

    # Audit entries included
    audit_entries: list[AuditEntry] = field(default_factory=list)

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at.isoformat(),
            "report_type": self.report_type,
            "period": {
                "start": self.period_start.isoformat(),
                "end": self.period_end.isoformat(),
            },
            "summary": {
                "total_decisions": self.total_decisions,
                "auto_executed": self.auto_executed,
                "human_reviewed": self.human_reviewed,
                "approved": self.approved,
                "rejected": self.rejected,
                "escalated": self.escalated,
                "sla_violations": self.sla_violations,
            },
            "risk_breakdown": {
                "critical": self.critical_decisions,
                "high": self.high_risk_decisions,
                "medium": self.medium_risk_decisions,
                "low": self.low_risk_decisions,
            },
            "operator_stats": {
                "unique_operators": self.unique_operators,
                "average_review_time_seconds": self.average_review_time,
            },
            "compliance_metrics": {
                "automation_rate": self.automation_rate,
                "human_oversight_rate": self.human_oversight_rate,
                "sla_compliance_rate": self.sla_compliance_rate,
            },
            "metadata": self.metadata,
        }
