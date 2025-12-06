"""
Recommendations for CANDI Core.

Action recommendations and HITL decision logic.
"""

from __future__ import annotations

from typing import List

from ..attribution_engine import AttributionResult
from ..forensic_analyzer import ForensicReport
from .models import ThreatLevel


class RecommendationMixin:
    """Mixin providing recommendation capabilities."""

    def _generate_recommendations(
        self,
        threat_level: ThreatLevel,
        attribution: AttributionResult,
        forensic: ForensicReport,
    ) -> List[str]:
        """Generate recommended actions based on analysis."""
        recommendations = []

        # Based on threat level
        if threat_level == ThreatLevel.APT:
            recommendations.extend([
                "CRITICAL: Potential APT activity detected",
                "Isolate affected systems immediately",
                "Notify security leadership",
                "Initiate incident response protocol",
                "Preserve all forensic evidence",
            ])
        elif threat_level == ThreatLevel.TARGETED:
            recommendations.extend([
                "HIGH: Targeted attack detected",
                "Review and strengthen defenses",
                "Monitor for related activity",
                "Update threat intelligence feeds",
            ])
        elif threat_level == ThreatLevel.OPPORTUNISTIC:
            recommendations.extend([
                "MEDIUM: Opportunistic attack detected",
                "Block identified IOCs",
                "Update signatures and rules",
            ])

        # Based on attribution
        if attribution.confidence > 70:
            recommendations.append(
                f"Attribution: {attribution.attributed_actor} "
                f"(confidence: {attribution.confidence}%)"
            )

        # Based on forensic findings
        if forensic.malware_detected:
            recommendations.append("Submit malware samples to sandbox for analysis")

        if forensic.credentials_compromised:
            recommendations.append("URGENT: Rotate compromised credentials")

        return recommendations

    def _requires_hitl_decision(
        self,
        threat_level: ThreatLevel,
        attribution: AttributionResult,
    ) -> bool:
        """Determine if human decision is required."""
        # Always require HITL for APT
        if threat_level == ThreatLevel.APT:
            return True

        # Require HITL for high-confidence attribution
        if attribution.confidence > 80:
            return True

        # Require HITL for targeted attacks
        if threat_level == ThreatLevel.TARGETED:
            return True

        return False
