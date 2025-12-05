"""Coordinator Models.

Data structures for Guardian Coordinator metrics and conflict resolution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..base import ConstitutionalViolation


@dataclass
class CoordinatorMetrics:
    """Metrics for Guardian Coordinator performance.

    Attributes:
        total_violations_detected: Total number of violations detected.
        violations_by_article: Count of violations by article.
        violations_by_severity: Count of violations by severity level.
        interventions_made: Total interventions made.
        vetos_enacted: Total vetos enacted.
        compliance_score: Overall compliance score (0-100).
        last_updated: Timestamp of last metrics update.
    """

    total_violations_detected: int = 0
    violations_by_article: dict[str, int] = field(default_factory=dict)
    violations_by_severity: dict[str, int] = field(default_factory=dict)
    interventions_made: int = 0
    vetos_enacted: int = 0
    compliance_score: float = 100.0
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary.

        Returns:
            Dictionary representation of metrics.
        """
        return {
            "total_violations_detected": self.total_violations_detected,
            "violations_by_article": self.violations_by_article,
            "violations_by_severity": self.violations_by_severity,
            "interventions_made": self.interventions_made,
            "vetos_enacted": self.vetos_enacted,
            "compliance_score": self.compliance_score,
            "last_updated": self.last_updated.isoformat(),
        }

    def update_compliance_score(self, assumed_successful_checks: int = 1000) -> None:
        """Update the compliance score based on violations.

        Args:
            assumed_successful_checks: Number of assumed successful checks.
        """
        total_checks = self.total_violations_detected + assumed_successful_checks
        if total_checks > 0:
            self.compliance_score = (
                (total_checks - self.total_violations_detected) / total_checks
            ) * 100
        self.last_updated = datetime.utcnow()


@dataclass
class ConflictResolution:
    """Resolution for conflicts between Guardian decisions.

    Attributes:
        conflict_id: Unique identifier for the conflict.
        guardian1_id: ID of first guardian involved.
        guardian2_id: ID of second guardian involved.
        violation1: First violation in conflict.
        violation2: Second violation in conflict.
        resolution: Resolution description.
        rationale: Reasoning for the resolution.
        timestamp: When the resolution was made.
    """

    conflict_id: str
    guardian1_id: str
    guardian2_id: str
    violation1: ConstitutionalViolation
    violation2: ConstitutionalViolation
    resolution: str
    rationale: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "conflict_id": self.conflict_id,
            "guardian1_id": self.guardian1_id,
            "guardian2_id": self.guardian2_id,
            "violation1": self.violation1.to_dict(),
            "violation2": self.violation2.to_dict(),
            "resolution": self.resolution,
            "rationale": self.rationale,
            "timestamp": self.timestamp.isoformat(),
        }
