"""
Priority Calculation Mixin for Decision Queue.

Handles priority score calculation for queue ordering.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..base_pkg import HITLDecision, RiskLevel


class PriorityMixin:
    """
    Mixin for priority calculation.

    Calculates priority scores based on risk level, threat score, and confidence.
    """

    def _calculate_priority(self, decision: HITLDecision) -> float:
        """
        Calculate priority score for decision.

        Higher score = higher priority.

        Args:
            decision: Decision to prioritize

        Returns:
            Priority score (0.0 to 1.0)
        """
        from ..base_pkg import RiskLevel

        # Base priority from risk level
        risk_priority = {
            RiskLevel.CRITICAL: 1.0,
            RiskLevel.HIGH: 0.75,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.LOW: 0.25,
        }[decision.risk_level]

        # Boost by threat score
        threat_boost = decision.context.threat_score * 0.1

        # Boost by confidence (higher confidence = slightly higher priority)
        confidence_boost = decision.context.confidence * 0.05

        total_priority = risk_priority + threat_boost + confidence_boost
        return min(1.0, total_priority)
