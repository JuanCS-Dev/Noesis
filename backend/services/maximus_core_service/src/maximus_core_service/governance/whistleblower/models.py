"""
Whistleblower Data Models.

Contains whistleblower report models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from ..enums import PolicySeverity, PolicyType


@dataclass
class WhistleblowerReport:
    """Whistleblower protection report."""

    report_id: str = field(default_factory=lambda: str(uuid4()))
    submission_date: datetime = field(default_factory=datetime.utcnow)
    reporter_id: str | None = None  # None if anonymous
    is_anonymous: bool = True
    title: str = ""
    description: str = ""
    alleged_violation_type: PolicyType = PolicyType.ETHICAL_USE
    severity: PolicySeverity = PolicySeverity.MEDIUM
    affected_systems: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)  # File paths or references
    status: str = "submitted"  # submitted, under_review, investigated, resolved, dismissed
    assigned_investigator: str | None = None
    investigation_notes: str = ""
    resolution: str = ""
    resolution_date: datetime | None = None
    escalated_to_erb: bool = False
    erb_decision_id: str | None = None
    retaliation_concerns: bool = False
    protection_measures: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_under_investigation(self) -> bool:
        """Check if report is currently under investigation."""
        return self.status in ["under_review", "investigated"]

    def is_resolved(self) -> bool:
        """Check if report is resolved."""
        return self.status in ["resolved", "dismissed"]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (redact sensitive info if anonymous)."""
        data = {
            "report_id": self.report_id,
            "submission_date": self.submission_date.isoformat(),
            "is_anonymous": self.is_anonymous,
            "title": self.title,
            "description": self.description,
            "alleged_violation_type": self.alleged_violation_type.value,
            "severity": self.severity.value,
            "affected_systems": self.affected_systems,
            "status": self.status,
            "resolution": self.resolution,
            "resolution_date": self.resolution_date.isoformat() if self.resolution_date else None,
            "escalated_to_erb": self.escalated_to_erb,
            "erb_decision_id": self.erb_decision_id,
            "retaliation_concerns": self.retaliation_concerns,
            "is_under_investigation": self.is_under_investigation(),
            "is_resolved": self.is_resolved(),
        }

        # Redact sensitive information for anonymous reports
        if not self.is_anonymous:
            data["reporter_id"] = self.reporter_id
            data["evidence"] = self.evidence
            data["investigation_notes"] = self.investigation_notes
            data["protection_measures"] = self.protection_measures

        return data
