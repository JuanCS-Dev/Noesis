"""
Risk Scoring Mixin.

Computes category-level risk scores from individual factors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..base_pkg import DecisionContext
    from .models import RiskFactors


class ScoringMixin:
    """
    Mixin for computing category-level risk scores.

    Aggregates individual factors into 6 category scores.
    """

    def _compute_threat_risk(self, factors: RiskFactors, context: DecisionContext) -> float:
        """
        Compute threat-related risk.

        Args:
            factors: Individual risk factors
            context: Decision context

        Returns:
            Threat risk score: 0.0 to 1.0
        """
        # Weight threat factors
        threat_risk = (
            0.5 * factors.threat_severity
            + 0.3 * (1.0 - factors.threat_confidence)  # Lower confidence = higher risk
            + 0.2 * factors.threat_novelty
        )
        return min(1.0, threat_risk)

    def _compute_asset_risk(self, factors: RiskFactors, context: DecisionContext) -> float:
        """
        Compute asset-related risk.

        Args:
            factors: Individual risk factors
            context: Decision context

        Returns:
            Asset risk score: 0.0 to 1.0
        """
        asset_risk = (
            0.5 * factors.asset_criticality + 0.3 * factors.data_sensitivity + 0.2 * factors.asset_count
        )
        return min(1.0, asset_risk)

    def _compute_business_risk(self, factors: RiskFactors, context: DecisionContext) -> float:
        """
        Compute business impact risk.

        Args:
            factors: Individual risk factors
            context: Decision context

        Returns:
            Business risk score: 0.0 to 1.0
        """
        business_risk = (
            0.4 * factors.financial_impact
            + 0.3 * factors.operational_impact
            + 0.3 * factors.reputational_impact
        )
        return min(1.0, business_risk)

    def _compute_action_risk(self, factors: RiskFactors, context: DecisionContext) -> float:
        """
        Compute action-related risk.

        Args:
            factors: Individual risk factors
            context: Decision context

        Returns:
            Action risk score: 0.0 to 1.0
        """
        action_risk = (
            0.5 * factors.action_reversibility
            + 0.3 * factors.action_aggressiveness
            + 0.2 * factors.action_scope
        )
        return min(1.0, action_risk)

    def _compute_compliance_risk(self, factors: RiskFactors, context: DecisionContext) -> float:
        """
        Compute compliance/regulatory risk.

        Args:
            factors: Individual risk factors
            context: Decision context

        Returns:
            Compliance risk score: 0.0 to 1.0
        """
        compliance_risk = 0.6 * factors.compliance_impact + 0.4 * factors.privacy_impact
        return min(1.0, compliance_risk)

    def _compute_environmental_risk(self, factors: RiskFactors, context: DecisionContext) -> float:
        """
        Compute environmental risk (time, availability, etc.).

        Args:
            factors: Individual risk factors
            context: Decision context

        Returns:
            Environmental risk score: 0.0 to 1.0
        """
        environmental_risk = 0.5 * factors.time_of_day + 0.5 * (
            1.0 - factors.operator_availability
        )  # Low availability = high risk
        return min(1.0, environmental_risk)
