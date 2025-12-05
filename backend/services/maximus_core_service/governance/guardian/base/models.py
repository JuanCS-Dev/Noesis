"""Guardian Data Models.

Dataclasses for constitutional violations, veto actions, interventions, decisions, and reports.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from .enums import ConstitutionalArticle, GuardianPriority, InterventionType


@dataclass
class ConstitutionalViolation:
    """Represents a detected violation of the Constitution.

    Attributes:
        violation_id: Unique identifier for the violation.
        article: Constitutional article violated.
        clause: Specific clause reference.
        rule: Specific rule violated.
        description: Description of the violation.
        severity: Priority level of the violation.
        detected_at: When the violation was detected.
        context: Additional context information.
        evidence: List of evidence strings.
        affected_systems: Systems affected by violation.
        recommended_action: Recommended remediation.
        metadata: Additional metadata.
    """

    violation_id: str = field(default_factory=lambda: str(uuid4()))
    article: ConstitutionalArticle = ConstitutionalArticle.ARTICLE_II
    clause: str = ""
    rule: str = ""
    description: str = ""
    severity: GuardianPriority = GuardianPriority.MEDIUM
    detected_at: datetime = field(default_factory=datetime.utcnow)
    context: dict[str, Any] = field(default_factory=dict)
    evidence: list[str] = field(default_factory=list)
    affected_systems: list[str] = field(default_factory=list)
    recommended_action: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "violation_id": self.violation_id,
            "article": self.article.value,
            "clause": self.clause,
            "rule": self.rule,
            "description": self.description,
            "severity": self.severity.value,
            "detected_at": self.detected_at.isoformat(),
            "context": self.context,
            "evidence": self.evidence,
            "affected_systems": self.affected_systems,
            "recommended_action": self.recommended_action,
            "metadata": self.metadata,
        }

    def generate_hash(self) -> str:
        """Generate unique hash for violation tracking.

        Returns:
            16-character hash string.
        """
        content = f"{self.article}{self.clause}{self.rule}{str(self.context)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class VetoAction:
    """Represents a veto action taken by a Guardian.

    Attributes:
        veto_id: Unique identifier for the veto.
        guardian_id: ID of the guardian that issued the veto.
        target_action: What action was vetoed.
        target_system: Which system/service.
        violation: Related violation if any.
        reason: Reason for the veto.
        enacted_at: When the veto was enacted.
        expires_at: When the veto expires.
        override_allowed: Whether override is allowed.
        override_requirements: Requirements to override.
        metadata: Additional metadata.
    """

    veto_id: str = field(default_factory=lambda: str(uuid4()))
    guardian_id: str = ""
    target_action: str = ""
    target_system: str = ""
    violation: ConstitutionalViolation | None = None
    reason: str = ""
    enacted_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    override_allowed: bool = False
    override_requirements: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_active(self) -> bool:
        """Check if veto is still active.

        Returns:
            True if veto is active.
        """
        if self.expires_at is None:
            return True
        return datetime.utcnow() < self.expires_at

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "veto_id": self.veto_id,
            "guardian_id": self.guardian_id,
            "target_action": self.target_action,
            "target_system": self.target_system,
            "violation": self.violation.to_dict() if self.violation else None,
            "reason": self.reason,
            "enacted_at": self.enacted_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active(),
            "override_allowed": self.override_allowed,
            "override_requirements": self.override_requirements,
            "metadata": self.metadata,
        }


@dataclass
class GuardianIntervention:
    """Records an intervention taken by a Guardian.

    Attributes:
        intervention_id: Unique identifier.
        guardian_id: ID of the guardian.
        intervention_type: Type of intervention.
        priority: Priority level.
        violation: Related violation if any.
        action_taken: Description of action taken.
        result: Result of the intervention.
        success: Whether intervention was successful.
        timestamp: When intervention occurred.
        metadata: Additional metadata.
    """

    intervention_id: str = field(default_factory=lambda: str(uuid4()))
    guardian_id: str = ""
    intervention_type: InterventionType = InterventionType.ALERT
    priority: GuardianPriority = GuardianPriority.MEDIUM
    violation: ConstitutionalViolation | None = None
    action_taken: str = ""
    result: str = ""
    success: bool = True
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "intervention_id": self.intervention_id,
            "guardian_id": self.guardian_id,
            "intervention_type": self.intervention_type.value,
            "priority": self.priority.value,
            "violation": self.violation.to_dict() if self.violation else None,
            "action_taken": self.action_taken,
            "result": self.result,
            "success": self.success,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class GuardianDecision:
    """Represents a decision made by a Guardian Agent.

    Attributes:
        decision_id: Unique identifier.
        guardian_id: ID of the guardian.
        decision_type: Type of decision.
        target: What the decision applies to.
        reasoning: Constitutional basis for decision.
        confidence: Confidence level (0.0 to 1.0).
        requires_validation: Whether validation is needed.
        timestamp: When decision was made.
        metadata: Additional metadata.
    """

    decision_id: str = field(default_factory=lambda: str(uuid4()))
    guardian_id: str = ""
    decision_type: str = ""
    target: str = ""
    reasoning: str = ""
    confidence: float = 0.0
    requires_validation: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "decision_id": self.decision_id,
            "guardian_id": self.guardian_id,
            "decision_type": self.decision_type,
            "target": self.target,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "requires_validation": self.requires_validation,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class GuardianReport:
    """Periodic compliance report from Guardian Agents.

    Attributes:
        report_id: Unique identifier.
        guardian_id: ID of the guardian.
        period_start: Report period start.
        period_end: Report period end.
        violations_detected: Number of violations.
        interventions_made: Number of interventions.
        vetos_enacted: Number of vetos.
        compliance_score: Compliance percentage.
        top_violations: List of top violations.
        recommendations: List of recommendations.
        metrics: Additional metrics.
        generated_at: When report was generated.
    """

    report_id: str = field(default_factory=lambda: str(uuid4()))
    guardian_id: str = ""
    period_start: datetime = field(default_factory=datetime.utcnow)
    period_end: datetime = field(default_factory=datetime.utcnow)
    violations_detected: int = 0
    interventions_made: int = 0
    vetos_enacted: int = 0
    compliance_score: float = 100.0
    top_violations: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "report_id": self.report_id,
            "guardian_id": self.guardian_id,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "violations_detected": self.violations_detected,
            "interventions_made": self.interventions_made,
            "vetos_enacted": self.vetos_enacted,
            "compliance_score": self.compliance_score,
            "top_violations": self.top_violations,
            "recommendations": self.recommendations,
            "metrics": self.metrics,
            "generated_at": self.generated_at.isoformat(),
        }
