"""
Core Risk Assessor Implementation.

Main risk assessment engine combining all risk analysis mixins.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .classification import ClassificationMixin
from .constants import RISK_WEIGHTS
from .factors import FactorComputationMixin
from .models import RiskScore
from .recommendations import RecommendationsMixin
from .scoring import ScoringMixin

if TYPE_CHECKING:
    from ..base_pkg import DecisionContext


class RiskAssessor(
    FactorComputationMixin,
    ScoringMixin,
    ClassificationMixin,
    RecommendationsMixin,
):
    """
    Comprehensive risk assessment engine.

    Analyzes security decisions across multiple risk dimensions and computes
    an overall risk score and level.

    Inherits from:
        - FactorComputationMixin: Individual factor assessment
        - ScoringMixin: Category-level scoring
        - ClassificationMixin: Risk level classification
        - RecommendationsMixin: Justifications and suggestions
    """

    def __init__(self) -> None:
        """Initialize risk assessor."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.WEIGHTS = RISK_WEIGHTS

    def assess_risk(self, context: DecisionContext) -> RiskScore:
        """
        Perform comprehensive risk assessment.

        Args:
            context: Decision context to assess

        Returns:
            RiskScore with overall score, level, and breakdown

        Process:
            1. Compute individual risk factors (16 factors)
            2. Compute category scores (6 categories)
            3. Compute weighted overall score
            4. Classify into risk level (CRITICAL/HIGH/MEDIUM/LOW)
            5. Generate justification and concerns
            6. Generate mitigation suggestions
        """
        # Compute individual risk factors
        factors = self._compute_risk_factors(context)

        # Compute category scores
        threat_risk = self._compute_threat_risk(factors, context)
        asset_risk = self._compute_asset_risk(factors, context)
        business_risk = self._compute_business_risk(factors, context)
        action_risk = self._compute_action_risk(factors, context)
        compliance_risk = self._compute_compliance_risk(factors, context)
        environmental_risk = self._compute_environmental_risk(factors, context)

        # Compute weighted overall score
        overall_score = (
            self.WEIGHTS["threat"] * threat_risk
            + self.WEIGHTS["asset"] * asset_risk
            + self.WEIGHTS["business"] * business_risk
            + self.WEIGHTS["action"] * action_risk
            + self.WEIGHTS["compliance"] * compliance_risk
            + self.WEIGHTS["environmental"] * environmental_risk
        )

        # Determine risk level
        risk_level = self._score_to_level(overall_score)

        # Generate justification and concerns
        justification, key_concerns = self._generate_justification(factors, overall_score, risk_level)

        # Generate recommendations
        mitigation_suggestions = self._generate_mitigation_suggestions(factors, context)

        # Build risk score
        risk_score = RiskScore(
            overall_score=overall_score,
            risk_level=risk_level,
            threat_risk=threat_risk,
            asset_risk=asset_risk,
            business_risk=business_risk,
            action_risk=action_risk,
            compliance_risk=compliance_risk,
            environmental_risk=environmental_risk,
            factors=factors,
            justification=justification,
            key_concerns=key_concerns,
            mitigation_suggestions=mitigation_suggestions,
        )

        self.logger.info(
            "Risk assessment complete: %s (score=%.2f, action=%s)",
            risk_level.value,
            overall_score,
            context.action_type.value,
        )

        return risk_score
