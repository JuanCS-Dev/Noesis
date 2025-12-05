"""
Ethical Guardian Models - Data classes and enums.

Contains all result dataclasses for the 7-phase ethical validation stack.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from compliance import RegulationType
from ethics import EthicalVerdict
from governance import PolicyType


class EthicalDecisionType(str, Enum):
    """Tipo de decisão ética final."""

    APPROVED = "approved"
    APPROVED_WITH_CONDITIONS = "approved_with_conditions"
    REJECTED_BY_GOVERNANCE = "rejected_by_governance"
    REJECTED_BY_ETHICS = "rejected_by_ethics"
    REJECTED_BY_FAIRNESS = "rejected_by_fairness"
    REJECTED_BY_PRIVACY = "rejected_by_privacy"
    REJECTED_BY_COMPLIANCE = "rejected_by_compliance"
    REQUIRES_HUMAN_REVIEW = "requires_human_review"
    ERROR = "error"


@dataclass
class GovernanceCheckResult:
    """Resultado do check de governance."""

    is_compliant: bool
    policies_checked: list[PolicyType]
    violations: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    duration_ms: float = 0.0


@dataclass
class EthicsCheckResult:
    """Resultado da avaliação ética."""

    verdict: EthicalVerdict
    confidence: float
    framework_results: list[dict[str, Any]] = field(default_factory=list)
    duration_ms: float = 0.0


@dataclass
class XAICheckResult:
    """Resultado da explicação XAI."""

    explanation_type: str
    summary: str
    feature_importances: list[dict[str, Any]] = field(default_factory=list)
    duration_ms: float = 0.0


@dataclass
class ComplianceCheckResult:
    """Resultado do check de compliance."""

    regulations_checked: list[RegulationType]
    compliance_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    overall_compliant: bool = True
    duration_ms: float = 0.0


@dataclass
class FairnessCheckResult:
    """Resultado do check de fairness e bias (Phase 3)."""

    fairness_ok: bool
    bias_detected: bool
    protected_attributes_checked: list[str]
    fairness_metrics: dict[str, float]
    bias_severity: str
    affected_groups: list[str] = field(default_factory=list)
    mitigation_recommended: bool = False
    confidence: float = 0.0
    duration_ms: float = 0.0


@dataclass
class PrivacyCheckResult:
    """Resultado do check de privacidade diferencial (Phase 4.1)."""

    privacy_budget_ok: bool
    privacy_level: str
    total_epsilon: float
    used_epsilon: float
    remaining_epsilon: float
    total_delta: float
    used_delta: float
    remaining_delta: float
    budget_exhausted: bool
    queries_executed: int
    duration_ms: float = 0.0


@dataclass
class FLCheckResult:
    """Resultado do check de federated learning (Phase 4.2)."""

    fl_ready: bool
    fl_status: str
    model_type: str | None = None
    aggregation_strategy: str | None = None
    requires_dp: bool = False
    dp_epsilon: float | None = None
    dp_delta: float | None = None
    notes: list[str] = field(default_factory=list)
    duration_ms: float = 0.0


@dataclass
class HITLCheckResult:
    """Resultado do check de HITL (Phase 5)."""

    requires_human_review: bool
    automation_level: str
    risk_level: str
    confidence_threshold_met: bool
    estimated_sla_minutes: int = 0
    escalation_recommended: bool = False
    human_expertise_required: list[str] = field(default_factory=list)
    decision_rationale: str = ""
    duration_ms: float = 0.0


@dataclass
class EthicalDecisionResult:
    """Resultado completo da decisão ética."""

    decision_id: str = field(default_factory=lambda: str(uuid4()))
    decision_type: EthicalDecisionType = EthicalDecisionType.ERROR
    action: str = ""
    actor: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Results from each phase
    governance: GovernanceCheckResult | None = None
    ethics: EthicsCheckResult | None = None
    fairness: FairnessCheckResult | None = None
    xai: XAICheckResult | None = None
    privacy: PrivacyCheckResult | None = None
    fl: FLCheckResult | None = None
    hitl: HITLCheckResult | None = None
    compliance: ComplianceCheckResult | None = None

    # Summary
    is_approved: bool = False
    conditions: list[str] = field(default_factory=list)
    rejection_reasons: list[str] = field(default_factory=list)

    # Performance
    total_duration_ms: float = 0.0

    # Audit
    audit_log_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "decision_id": self.decision_id,
            "decision_type": self.decision_type.value,
            "action": self.action,
            "actor": self.actor,
            "timestamp": self.timestamp.isoformat(),
            "is_approved": self.is_approved,
            "conditions": self.conditions,
            "rejection_reasons": self.rejection_reasons,
            "total_duration_ms": self.total_duration_ms,
            "audit_log_id": self.audit_log_id,
            "governance": {
                "is_compliant": self.governance.is_compliant if self.governance else False,
                "policies_checked": [
                    p.value for p in self.governance.policies_checked
                ] if self.governance else [],
                "violations_count": len(self.governance.violations) if self.governance else 0,
            }
            if self.governance
            else None,
            "ethics": {
                "verdict": self.ethics.verdict.value if self.ethics else "unknown",
                "confidence": self.ethics.confidence if self.ethics else 0.0,
                "frameworks_count": len(self.ethics.framework_results) if self.ethics else 0,
            }
            if self.ethics
            else None,
            "xai": {
                "summary": self.xai.summary if self.xai else "",
                "features_count": len(self.xai.feature_importances) if self.xai else 0,
            }
            if self.xai
            else None,
            "compliance": {
                "overall_compliant": self.compliance.overall_compliant if self.compliance else False,
                "regulations_checked": len(self.compliance.regulations_checked) if self.compliance else 0,
            }
            if self.compliance
            else None,
        }
