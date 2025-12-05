"""
Risk Factor Computation Mixin.

Computes individual risk factors from decision context.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from .constants import (
    ACTION_AGGRESSIVENESS,
    ACTION_REVERSIBILITY,
    CRITICALITY_SCORES,
    OPERATIONAL_IMPACT_KEYWORDS,
    SCOPE_SCORES,
    SENSITIVITY_SCORES,
)
from .models import RiskFactors

if TYPE_CHECKING:
    from ..base_pkg import DecisionContext


class FactorComputationMixin:
    """
    Mixin for computing individual risk factors.

    Provides methods to assess all 16 risk factors from decision context.
    """

    def _compute_risk_factors(self, context: DecisionContext) -> RiskFactors:
        """
        Compute individual risk factors from context.

        Args:
            context: Decision context

        Returns:
            RiskFactors with all 16 factors computed
        """
        factors = RiskFactors()

        # Threat factors
        factors.threat_severity = context.threat_score
        factors.threat_confidence = context.confidence
        factors.threat_novelty = self._assess_threat_novelty(context)

        # Asset factors
        factors.asset_criticality = self._assess_asset_criticality(context)
        factors.asset_count = self._normalize_asset_count(len(context.affected_assets))
        factors.data_sensitivity = self._assess_data_sensitivity(context)

        # Business factors
        factors.financial_impact = self._normalize_financial_impact(context.estimated_cost)
        factors.operational_impact = self._assess_operational_impact(context)
        factors.reputational_impact = self._assess_reputational_impact(context)

        # Action factors
        factors.action_reversibility = ACTION_REVERSIBILITY.get(context.action_type, 0.5)
        factors.action_aggressiveness = ACTION_AGGRESSIVENESS.get(context.action_type, 0.5)
        factors.action_scope = self._assess_action_scope(context)

        # Compliance factors
        factors.compliance_impact = self._assess_compliance_impact(context)
        factors.privacy_impact = self._assess_privacy_impact(context)

        # Environmental factors
        factors.time_of_day = self._assess_time_of_day()
        factors.operator_availability = self._assess_operator_availability()

        return factors

    def _assess_threat_novelty(self, context: DecisionContext) -> float:
        """
        Assess if threat is novel/unknown.

        Args:
            context: Decision context

        Returns:
            Novelty score: 0.0 (known) to 1.0 (novel)
        """
        # Check if threat has similar past incidents
        if context.similar_past_decisions:
            return 0.2  # Known threat pattern
        if context.threat_type in ["zero_day", "unknown", "novel"]:
            return 0.9  # Novel threat
        return 0.5  # Moderately novel

    def _assess_asset_criticality(self, context: DecisionContext) -> float:
        """
        Assess criticality of affected assets.

        Args:
            context: Decision context

        Returns:
            Criticality score: 0.0 to 1.0
        """
        return CRITICALITY_SCORES.get(context.asset_criticality.lower(), 0.5)

    def _normalize_asset_count(self, count: int) -> float:
        """
        Normalize asset count to 0-1 scale.

        Args:
            count: Number of affected assets

        Returns:
            Normalized score: 0.0 to 1.0
        """
        # 1 asset = 0.1, 10 assets = 0.5, 100+ assets = 1.0
        if count <= 1:
            return 0.1
        if count <= 10:
            return 0.1 + (count - 1) * 0.044  # Linear 0.1 to 0.5
        if count <= 100:
            return 0.5 + (count - 10) * 0.0056  # Linear 0.5 to 1.0
        return 1.0

    def _assess_data_sensitivity(self, context: DecisionContext) -> float:
        """
        Assess sensitivity of data on affected assets.

        Args:
            context: Decision context

        Returns:
            Sensitivity score: 0.0 to 1.0
        """
        # Check metadata for data classification
        data_class = context.metadata.get("data_classification", "internal")
        return SENSITIVITY_SCORES.get(data_class.lower(), 0.5)

    def _normalize_financial_impact(self, cost: float) -> float:
        """
        Normalize financial impact to 0-1 scale.

        Args:
            cost: Estimated cost in dollars

        Returns:
            Normalized score: 0.0 to 1.0
        """
        # $0 = 0.0, $10K = 0.3, $100K = 0.6, $1M+ = 1.0
        if cost <= 0:
            return 0.0
        if cost < 10000:
            return cost / 33333  # Linear 0 to 0.3
        if cost < 100000:
            return 0.3 + (cost - 10000) / 300000  # Linear 0.3 to 0.6
        if cost < 1000000:
            return 0.6 + (cost - 100000) / 2250000  # Linear 0.6 to 1.0
        return 1.0

    def _assess_operational_impact(self, context: DecisionContext) -> float:
        """
        Assess impact on business operations.

        Args:
            context: Decision context

        Returns:
            Operational impact score: 0.0 to 1.0
        """
        business_impact = context.business_impact.lower()
        for keyword, score in OPERATIONAL_IMPACT_KEYWORDS.items():
            if keyword in business_impact:
                return score
        return 0.5  # Default moderate

    def _assess_reputational_impact(self, context: DecisionContext) -> float:
        """
        Assess potential reputational damage.

        Args:
            context: Decision context

        Returns:
            Reputational impact score: 0.0 to 1.0
        """
        # High for public-facing assets, data breaches
        if "public" in context.metadata.get("asset_type", ""):
            return 0.7
        if "customer_data" in context.metadata.get("data_type", ""):
            return 0.8
        return 0.3

    def _assess_action_scope(self, context: DecisionContext) -> float:
        """
        Assess scope of action.

        Args:
            context: Decision context

        Returns:
            Scope score: 0.0 (local) to 1.0 (global)
        """
        scope = context.action_params.get("scope", "local")
        return SCOPE_SCORES.get(scope, 0.1)

    def _assess_compliance_impact(self, context: DecisionContext) -> float:
        """
        Assess regulatory/compliance implications.

        Args:
            context: Decision context

        Returns:
            Compliance impact score: 0.0 to 1.0
        """
        # Check for compliance tags
        compliance_tags = context.metadata.get("compliance_tags", [])
        if any(tag in compliance_tags for tag in ["hipaa", "gdpr", "pci-dss"]):
            return 0.9  # High compliance impact
        if compliance_tags:
            return 0.6  # Some compliance requirements
        return 0.2  # Minimal compliance impact

    def _assess_privacy_impact(self, context: DecisionContext) -> float:
        """
        Assess PII/privacy implications.

        Args:
            context: Decision context

        Returns:
            Privacy impact score: 0.0 to 1.0
        """
        if "pii" in context.metadata.get("data_type", ""):
            return 0.9
        if "user_data" in context.metadata.get("data_type", ""):
            return 0.6
        return 0.2

    def _assess_time_of_day(self) -> float:
        """
        Assess risk based on time of day.

        Returns:
            Time risk score: 0.0 to 1.0 (higher outside business hours)
        """
        hour = datetime.utcnow().hour
        # Business hours (9-17 UTC): low risk
        # Outside hours: higher risk due to reduced oversight
        if 9 <= hour < 17:
            return 0.2  # Business hours
        if 17 <= hour < 22 or 6 <= hour < 9:
            return 0.5  # Evening/early morning
        return 0.8  # Night (22-6)

    def _assess_operator_availability(self) -> float:
        """
        Assess operator availability.

        Returns:
            Availability score: 0.0 (none) to 1.0 (full)
        """
        # In production, this would check actual operator shifts/availability
        # For now, use time-based heuristic
        hour = datetime.utcnow().hour
        if 9 <= hour < 17:
            return 0.9  # Business hours
        if 17 <= hour < 22:
            return 0.6  # Evening shift
        return 0.3  # Night shift (limited)
