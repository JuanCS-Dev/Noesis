"""ADW #3: Target Profiling Models.

Data models for target profiling workflow.

Authors: MAXIMUS Team
Date: 2025-10-15
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


class SEVulnerability(Enum):
    """Social engineering vulnerability level."""

    CRITICAL = "critical"  # Highly susceptible, immediate risk
    HIGH = "high"  # Multiple risk factors identified
    MEDIUM = "medium"  # Some exposure, manageable risk
    LOW = "low"  # Minimal exposure
    INFO = "info"  # Informational only


@dataclass
class ProfileTarget:
    """Target for deep profiling."""

    username: str | None = None
    email: str | None = None
    phone: str | None = None
    name: str | None = None
    location: str | None = None
    image_url: str | None = None
    include_social: bool = True
    include_images: bool = True


@dataclass
class ProfileFinding:
    """Individual profiling finding."""

    finding_id: str
    finding_type: str  # contact, social, platform, image, pattern, behavior
    category: str
    details: dict[str, Any]
    timestamp: str
    confidence: float = 1.0


@dataclass
class TargetProfileReport:
    """Complete target profiling report."""

    workflow_id: str
    target_username: str | None
    target_email: str | None
    target_name: str | None
    status: WorkflowStatus
    started_at: str
    completed_at: str | None
    findings: list[ProfileFinding] = field(default_factory=list)
    contact_info: dict[str, Any] = field(default_factory=dict)
    social_profiles: list[dict[str, Any]] = field(default_factory=list)
    platform_presence: list[str] = field(default_factory=list)
    behavioral_patterns: list[dict[str, Any]] = field(default_factory=list)
    locations: list[dict[str, Any]] = field(default_factory=list)
    se_vulnerability: SEVulnerability = SEVulnerability.INFO
    se_score: float = 0.0
    recommendations: list[str] = field(default_factory=list)
    statistics: dict[str, Any] = field(default_factory=dict)
    ai_analysis: dict[str, Any] | None = field(default=None)
    error: str | None = field(default=None)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "target_username": self.target_username,
            "target_email": self.target_email,
            "target_name": self.target_name,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "findings": [asdict(f) for f in self.findings],
            "contact_info": self.contact_info,
            "social_profiles": self.social_profiles,
            "platform_presence": self.platform_presence,
            "behavioral_patterns": self.behavioral_patterns,
            "locations": self.locations,
            "se_vulnerability": self.se_vulnerability.value,
            "se_score": self.se_score,
            "recommendations": self.recommendations,
            "statistics": self.statistics,
            "ai_analysis": self.ai_analysis,
            "error": self.error,
        }
