"""
Risk Classification Mixin.

Converts numeric risk scores to discrete risk levels.
"""

from __future__ import annotations

from ..base_pkg import RiskLevel
from .constants import CRITICAL_THRESHOLD, HIGH_THRESHOLD, MEDIUM_THRESHOLD


class ClassificationMixin:
    """
    Mixin for classifying risk scores into levels.

    Provides method to convert numeric score to CRITICAL/HIGH/MEDIUM/LOW.
    """

    def _score_to_level(self, score: float) -> RiskLevel:
        """
        Convert numeric score to risk level.

        Args:
            score: Overall risk score (0.0 to 1.0)

        Returns:
            RiskLevel enum value

        Classification:
            - score >= 0.75 → CRITICAL
            - score >= 0.50 → HIGH
            - score >= 0.30 → MEDIUM
            - score <  0.30 → LOW
        """
        if score >= CRITICAL_THRESHOLD:
            return RiskLevel.CRITICAL
        if score >= HIGH_THRESHOLD:
            return RiskLevel.HIGH
        if score >= MEDIUM_THRESHOLD:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
