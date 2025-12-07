"""Compliance Engine Models.

Data structures for compliance check results and snapshots.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from ..base import (
    ComplianceResult,
    ComplianceViolation,
    RegulationType,
    ViolationSeverity,
)


@dataclass
class ComplianceCheckResult:
    """Result of running compliance check for a regulation.

    Attributes:
        regulation_type: Type of regulation checked.
        checked_at: Timestamp of check.
        total_controls: Total number of controls.
        controls_checked: Number of controls checked.
        compliant: Number of compliant controls.
        non_compliant: Number of non-compliant controls.
        partially_compliant: Number of partially compliant controls.
        not_applicable: Number of not applicable controls.
        pending_review: Number pending manual review.
        evidence_required: Number requiring evidence.
        results: List of individual control results.
        violations: List of detected violations.
        compliance_percentage: Percentage of compliant controls.
        score: Weighted compliance score (0.0-1.0).
    """

    regulation_type: RegulationType
    checked_at: datetime
    total_controls: int
    controls_checked: int
    compliant: int
    non_compliant: int
    partially_compliant: int
    not_applicable: int
    pending_review: int
    evidence_required: int
    results: list[ComplianceResult] = field(default_factory=list)
    violations: list[ComplianceViolation] = field(default_factory=list)
    compliance_percentage: float = 0.0
    score: float = 0.0

    def __post_init__(self) -> None:
        """Calculate metrics after initialization."""
        if self.total_controls > 0:
            self.compliance_percentage = (self.compliant / self.total_controls) * 100

            weighted_sum = (
                (self.compliant * 1.0)
                + (self.partially_compliant * 0.5)
                + (self.non_compliant * 0.0)
                + (self.not_applicable * 1.0)
            )
            applicable_controls = self.total_controls - self.not_applicable
            if applicable_controls > 0:
                self.score = weighted_sum / applicable_controls
            else:
                self.score = 1.0

    def is_certification_ready(self, threshold: float = 95.0) -> bool:
        """Check if compliance meets certification threshold.

        Args:
            threshold: Minimum compliance percentage.

        Returns:
            True if compliance percentage meets threshold.
        """
        return self.compliance_percentage >= threshold

    def get_critical_violations(self) -> list[ComplianceViolation]:
        """Get critical severity violations.

        Returns:
            List of critical violations.
        """
        return [v for v in self.violations if v.severity == ViolationSeverity.CRITICAL]


@dataclass
class ComplianceSnapshot:
    """Point-in-time snapshot of overall compliance status.

    Attributes:
        snapshot_id: Unique identifier for the snapshot.
        timestamp: When the snapshot was taken.
        regulation_results: Results by regulation type.
        overall_compliance_percentage: Average compliance across regulations.
        overall_score: Average weighted score.
        total_violations: Total number of violations.
        critical_violations: Number of critical violations.
    """

    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    regulation_results: dict[RegulationType, ComplianceCheckResult] = field(
        default_factory=dict
    )
    overall_compliance_percentage: float = 0.0
    overall_score: float = 0.0
    total_violations: int = 0
    critical_violations: int = 0

    def __post_init__(self) -> None:
        """Calculate overall metrics after initialization."""
        if self.regulation_results:
            percentages = [r.compliance_percentage for r in self.regulation_results.values()]
            self.overall_compliance_percentage = sum(percentages) / len(percentages)

            scores = [r.score for r in self.regulation_results.values()]
            self.overall_score = sum(scores) / len(scores)

            for result in self.regulation_results.values():
                self.total_violations += len(result.violations)
                self.critical_violations += len(result.get_critical_violations())
