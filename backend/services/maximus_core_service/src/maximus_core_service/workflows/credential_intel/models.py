"""Credential Intelligence Models.

Data models for credential intelligence workflow.
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


class CredentialRiskLevel(Enum):
    """Credential exposure risk level."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class CredentialTarget:
    """Target for credential intelligence gathering."""

    email: str | None = None
    username: str | None = None
    phone: str | None = None
    include_darkweb: bool = True
    include_dorking: bool = True
    include_social: bool = True


@dataclass
class CredentialFinding:
    """Individual credential exposure finding."""

    finding_id: str
    finding_type: str
    severity: CredentialRiskLevel
    source: str
    details: dict[str, Any]
    timestamp: str
    confidence: float = 1.0


@dataclass
class CredentialIntelReport:
    """Complete credential intelligence report."""

    workflow_id: str
    target_email: str | None
    target_username: str | None
    status: WorkflowStatus
    started_at: str
    completed_at: str | None
    findings: list[CredentialFinding] = field(default_factory=list)
    exposure_score: float = 0.0
    breach_count: int = 0
    platform_presence: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    statistics: dict[str, Any] = field(default_factory=dict)
    ai_analysis: dict[str, Any] | None = field(default=None)
    error: str | None = field(default=None)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "target_email": self.target_email,
            "target_username": self.target_username,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "findings": [
                {**asdict(f), "severity": f.severity.value} for f in self.findings
            ],
            "exposure_score": self.exposure_score,
            "breach_count": self.breach_count,
            "platform_presence": self.platform_presence,
            "recommendations": self.recommendations,
            "statistics": self.statistics,
            "ai_analysis": self.ai_analysis,
            "error": self.error,
        }
