"""
Risk Recommendations Mixin.

Generates justifications and mitigation suggestions for risk assessments.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..base_pkg import RiskLevel

if TYPE_CHECKING:
    from ..base_pkg import DecisionContext
    from .models import RiskFactors


class RecommendationsMixin:
    """
    Mixin for generating risk justifications and recommendations.

    Provides human-readable explanations and mitigation suggestions.
    """

    def _generate_justification(
        self, factors: RiskFactors, score: float, level: RiskLevel
    ) -> tuple[str, list[str]]:
        """
        Generate human-readable justification for risk assessment.

        Args:
            factors: Individual risk factors
            score: Overall risk score
            level: Classified risk level

        Returns:
            Tuple of (justification_text, key_concerns_list)
        """
        concerns = []

        # Identify high-risk factors (>0.7)
        all_factors = factors.get_all_factors()
        for factor_name, factor_value in all_factors.items():
            if factor_value >= 0.7:
                concerns.append(f"{factor_name.replace('_', ' ').title()}: {factor_value:.1%}")

        # Generate justification
        if level == RiskLevel.CRITICAL:
            justification = (
                f"CRITICAL RISK (score={score:.2f}): Multiple high-risk factors identified. "
                f"Immediate executive oversight required."
            )
        elif level == RiskLevel.HIGH:
            justification = (
                f"HIGH RISK (score={score:.2f}): Significant risk factors present. "
                f"Senior operator approval required."
            )
        elif level == RiskLevel.MEDIUM:
            justification = f"MEDIUM RISK (score={score:.2f}): Moderate risk. Operator review recommended."
        else:
            justification = f"LOW RISK (score={score:.2f}): Minimal risk factors. May proceed with supervision."

        return justification, concerns

    def _generate_mitigation_suggestions(
        self, factors: RiskFactors, context: DecisionContext
    ) -> list[str]:
        """
        Generate risk mitigation suggestions.

        Args:
            factors: Individual risk factors
            context: Decision context

        Returns:
            List of mitigation suggestion strings
        """
        suggestions = []

        if factors.threat_confidence < 0.7:
            suggestions.append("Collect additional threat intelligence before acting")

        if factors.asset_criticality >= 0.8:
            suggestions.append("Consider isolating critical assets during investigation")

        if factors.action_reversibility >= 0.7:
            suggestions.append("Backup data before executing irreversible action")

        if factors.compliance_impact >= 0.7:
            suggestions.append("Consult legal/compliance team before proceeding")

        if factors.operator_availability < 0.3:
            suggestions.append("Wait for operator availability or escalate immediately")

        return suggestions
