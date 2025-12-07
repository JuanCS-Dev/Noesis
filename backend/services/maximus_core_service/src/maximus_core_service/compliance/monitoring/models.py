"""Compliance Monitoring Models.

Data structures for compliance alerts and monitoring metrics.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..base import (
    RegulationType,
    ViolationSeverity,
)


@dataclass
class ComplianceAlert:
    """Compliance alert notification.

    Attributes:
        alert_id: Unique identifier.
        alert_type: Type of alert.
        severity: Alert severity.
        title: Alert title.
        message: Alert message.
        regulation_type: Related regulation if any.
        triggered_at: When alert was triggered.
        acknowledged: Whether alert is acknowledged.
        acknowledged_by: Who acknowledged.
        acknowledged_at: When acknowledged.
        metadata: Additional metadata.
    """

    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    alert_type: str = ""
    severity: ViolationSeverity = ViolationSeverity.MEDIUM
    title: str = ""
    message: str = ""
    regulation_type: RegulationType | None = None
    triggered_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    acknowledged_by: str | None = None
    acknowledged_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def acknowledge(self, acknowledged_by: str) -> None:
        """Mark alert as acknowledged.

        Args:
            acknowledged_by: User acknowledging the alert.
        """
        self.acknowledged = True
        self.acknowledged_by = acknowledged_by
        self.acknowledged_at = datetime.utcnow()


@dataclass
class MonitoringMetrics:
    """Compliance monitoring metrics snapshot.

    Attributes:
        snapshot_id: Unique identifier.
        timestamp: When metrics were captured.
        overall_compliance_percentage: Overall compliance percentage.
        overall_score: Overall compliance score.
        compliance_by_regulation: Compliance by regulation type.
        total_violations: Total number of violations.
        critical_violations: Number of critical violations.
        high_violations: Number of high violations.
        medium_violations: Number of medium violations.
        low_violations: Number of low violations.
        total_evidence: Total evidence count.
        expired_evidence: Expired evidence count.
        expiring_soon_evidence: Evidence expiring in 30 days.
        remediation_plans_active: Active remediation plans.
        remediation_actions_overdue: Overdue actions.
        compliance_trend: Trend indicator.
    """

    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    overall_compliance_percentage: float = 0.0
    overall_score: float = 0.0
    compliance_by_regulation: dict[str, float] = field(default_factory=dict)
    total_violations: int = 0
    critical_violations: int = 0
    high_violations: int = 0
    medium_violations: int = 0
    low_violations: int = 0
    total_evidence: int = 0
    expired_evidence: int = 0
    expiring_soon_evidence: int = 0
    remediation_plans_active: int = 0
    remediation_actions_overdue: int = 0
    compliance_trend: str = "stable"
