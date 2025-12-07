"""Attack Surface Models.

Data models for attack surface mapping workflow.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class WorkflowStatus(Enum):
    """Workflow execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskLevel(Enum):
    """Risk level classification."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class AttackSurfaceTarget:
    """Target for attack surface mapping.

    Attributes:
        domain: Target domain name.
        include_subdomains: Whether to enumerate subdomains.
        port_range: Port range specification.
        scan_depth: Scan depth level.
    """

    domain: str
    include_subdomains: bool = True
    port_range: str | None = None
    scan_depth: str = "standard"


@dataclass
class Finding:
    """Individual attack surface finding.

    Attributes:
        finding_id: Unique finding identifier.
        finding_type: Type of finding.
        severity: Risk level severity.
        target: Target that was scanned.
        details: Additional finding details.
        timestamp: When finding was discovered.
        confidence: Confidence score.
    """

    finding_id: str
    finding_type: str
    severity: RiskLevel
    target: str
    details: dict[str, Any]
    timestamp: str
    confidence: float = 1.0


@dataclass
class AttackSurfaceReport:
    """Complete attack surface mapping report.

    Attributes:
        workflow_id: Unique workflow identifier.
        target: Target domain.
        status: Workflow status.
        started_at: Workflow start time.
        completed_at: Workflow completion time.
        findings: List of findings.
        statistics: Findings statistics.
        risk_score: Overall risk score.
        recommendations: Remediation recommendations.
        ai_analysis: AI-powered analysis results.
        error: Error message if failed.
    """

    workflow_id: str
    target: str
    status: WorkflowStatus
    started_at: str
    completed_at: str | None
    findings: list[Finding] = field(default_factory=list)
    statistics: dict[str, Any] = field(default_factory=dict)
    risk_score: float = 0.0
    recommendations: list[str] = field(default_factory=list)
    ai_analysis: dict[str, Any] | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of report.
        """
        return {
            "workflow_id": self.workflow_id,
            "target": self.target,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "findings": [
                {**asdict(f), "severity": f.severity.value} for f in self.findings
            ],
            "statistics": self.statistics,
            "risk_score": self.risk_score,
            "recommendations": self.recommendations,
            "ai_analysis": self.ai_analysis,
            "error": self.error,
        }
