"""
Scoring Functions for Threat Intelligence.

Threat score and confidence calculation.
"""

from __future__ import annotations

from typing import List

from ..forensic_analyzer import ForensicReport
from .models import ThreatIntelReport


class ScoringMixin:
    """Mixin providing scoring capabilities."""

    def _calculate_threat_score(
        self,
        report: ThreatIntelReport,
        forensic: ForensicReport,
    ) -> float:
        """
        Calculate overall threat score (0-100).

        Factors:
        - Known malicious IOCs: +30
        - Known tools/malware: +25
        - Known exploits: +20
        - Campaign correlation: +15
        - Forensic sophistication: +10
        """
        score = 0.0

        # Known IOCs
        if report.known_iocs:
            # Check for malicious reputation
            malicious_count = sum(
                1 for rep in report.ioc_reputation.values()
                if rep in ['malicious', 'high_threat']
            )
            if malicious_count:
                score += min(30.0, malicious_count * 10)

        # Known tools
        if report.known_tools:
            score += min(25.0, len(report.known_tools) * 8)

        # Known exploits
        if report.known_exploits:
            score += min(20.0, len(report.known_exploits) * 10)

        # Campaign correlation
        if report.related_campaigns:
            score += min(15.0, len(report.related_campaigns) * 7)

        # Forensic sophistication bonus
        if forensic.sophistication_score >= 7:
            score += 10.0

        return min(score, 100.0)

    def _get_sources_used(self, report: ThreatIntelReport) -> List[str]:
        """Get list of intelligence sources used."""
        sources = ['local_ioc_database']

        if report.known_tools:
            sources.append('tool_database')

        if report.known_exploits:
            sources.append('cve_database')

        if report.related_campaigns:
            sources.append('campaign_database')

        if report.misp_events:
            sources.append('misp_platform')

        return sources

    def _calculate_confidence(self, report: ThreatIntelReport) -> float:
        """Calculate correlation confidence (0-100%)."""
        confidence = 0.0

        # Multiple sources = higher confidence
        confidence += len(report.intelligence_sources) * 10

        # Known IOCs = high confidence
        if report.known_iocs:
            confidence += 30

        # Known tools = high confidence
        if report.known_tools:
            confidence += 25

        # MISP correlation = high confidence
        if report.misp_events:
            confidence += 20

        return min(confidence, 100.0)
