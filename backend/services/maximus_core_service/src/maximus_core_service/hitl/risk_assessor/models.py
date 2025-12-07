"""
Risk Assessment Data Models.

Contains risk factors and risk score data structures.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..base_pkg import RiskLevel


@dataclass
class RiskFactors:
    """
    Individual risk factors that contribute to overall risk score.

    Each factor is scored 0.0 (low risk) to 1.0 (high risk).
    """

    # Threat factors
    threat_severity: float = 0.0  # Threat score from detection engine
    threat_confidence: float = 0.0  # Confidence in threat identification
    threat_novelty: float = 0.0  # Is this a new/unknown threat?

    # Asset factors
    asset_criticality: float = 0.0  # Business criticality of assets
    asset_count: float = 0.0  # Number of affected assets (normalized)
    data_sensitivity: float = 0.0  # Sensitivity of data on assets

    # Business factors
    financial_impact: float = 0.0  # Estimated financial loss
    operational_impact: float = 0.0  # Impact on operations
    reputational_impact: float = 0.0  # Reputation/brand damage

    # Action factors
    action_reversibility: float = 0.0  # Can action be undone? (0=fully reversible)
    action_aggressiveness: float = 0.0  # How aggressive is action?
    action_scope: float = 0.0  # Scope of action (local vs global)

    # Compliance factors
    compliance_impact: float = 0.0  # Regulatory/compliance implications
    privacy_impact: float = 0.0  # Privacy/PII implications

    # Environmental factors
    time_of_day: float = 0.0  # Higher risk outside business hours
    operator_availability: float = 0.0  # Are operators available?

    def get_all_factors(self) -> dict[str, float]:
        """Get all risk factors as dict."""
        return {
            "threat_severity": self.threat_severity,
            "threat_confidence": self.threat_confidence,
            "threat_novelty": self.threat_novelty,
            "asset_criticality": self.asset_criticality,
            "asset_count": self.asset_count,
            "data_sensitivity": self.data_sensitivity,
            "financial_impact": self.financial_impact,
            "operational_impact": self.operational_impact,
            "reputational_impact": self.reputational_impact,
            "action_reversibility": self.action_reversibility,
            "action_aggressiveness": self.action_aggressiveness,
            "action_scope": self.action_scope,
            "compliance_impact": self.compliance_impact,
            "privacy_impact": self.privacy_impact,
            "time_of_day": self.time_of_day,
            "operator_availability": self.operator_availability,
        }

    def get_max_factor(self) -> tuple[str, float]:
        """Get highest risk factor."""
        factors = self.get_all_factors()
        max_factor = max(factors.items(), key=lambda x: x[1])
        return max_factor


@dataclass
class RiskScore:
    """
    Computed risk score with breakdown by category.
    """

    # Overall risk score (0.0 to 1.0)
    overall_score: float = 0.0

    # Risk level
    risk_level: RiskLevel = RiskLevel.LOW

    # Category scores
    threat_risk: float = 0.0
    asset_risk: float = 0.0
    business_risk: float = 0.0
    action_risk: float = 0.0
    compliance_risk: float = 0.0
    environmental_risk: float = 0.0

    # Contributing factors
    factors: RiskFactors = field(default_factory=RiskFactors)

    # Risk justification
    justification: str = ""
    key_concerns: list[str] = field(default_factory=list)

    # Recommendations
    recommended_automation: str | None = None
    mitigation_suggestions: list[str] = field(default_factory=list)

    def get_category_breakdown(self) -> dict[str, float]:
        """Get risk breakdown by category."""
        return {
            "threat": self.threat_risk,
            "asset": self.asset_risk,
            "business": self.business_risk,
            "action": self.action_risk,
            "compliance": self.compliance_risk,
            "environmental": self.environmental_risk,
        }

    def get_summary(self) -> str:
        """Get human-readable risk summary."""
        parts = [
            f"Risk Level: {self.risk_level.value.upper()}",
            f"Score: {self.overall_score:.2f}",
        ]

        if self.key_concerns:
            parts.append(f"Concerns: {', '.join(self.key_concerns[:3])}")

        return " | ".join(parts)


# Risk weights for category scoring
RISK_WEIGHTS = {
    "threat": 0.30,
    "asset": 0.20,
    "business": 0.20,
    "action": 0.15,
    "compliance": 0.10,
    "environmental": 0.05,
}

# Risk level thresholds
RISK_THRESHOLDS = {
    "critical": 0.80,
    "high": 0.60,
    "medium": 0.40,
    "low": 0.20,
}

# Sensitivity score mapping
SENSITIVITY_SCORES = {
    "public": 0.0,
    "internal": 0.3,
    "confidential": 0.6,
    "restricted": 0.9,
}

# Criticality score mapping
CRITICALITY_SCORES = {
    "low": 0.2,
    "medium": 0.5,
    "high": 0.8,
    "critical": 1.0,
}
