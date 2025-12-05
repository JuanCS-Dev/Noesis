"""
Classification Functions for CANDI Core.

Threat level classification, IOC extraction, MITRE ATT&CK mapping.
"""

from __future__ import annotations

from typing import List

from ..attribution_engine import AttributionResult
from ..forensic_analyzer import ForensicReport
from ..threat_intelligence import ThreatIntelReport
from .models import ThreatLevel


class ClassificationMixin:
    """Mixin providing classification capabilities."""

    def _classify_threat_level(
        self,
        forensic: ForensicReport,
        intel: ThreatIntelReport,
        attribution: AttributionResult,
    ) -> ThreatLevel:
        """
        Classify threat level based on analysis.

        Args:
            forensic: Forensic analysis report
            intel: Threat intelligence report
            attribution: Attribution result

        Returns:
            Threat level classification
        """
        # APT indicators
        if attribution.apt_indicators:
            return ThreatLevel.APT

        # Known APT actor
        if attribution.attributed_actor and "APT" in attribution.attributed_actor:
            return ThreatLevel.APT

        # High sophistication + known tools
        if forensic.sophistication_score > 8 and intel.known_tools:
            return ThreatLevel.TARGETED

        # Custom exploits or zero-days
        if "zero_day" in forensic.behaviors or "custom_exploit" in forensic.behaviors:
            return ThreatLevel.TARGETED

        # Known exploits or tools
        if intel.known_exploits or forensic.malware_detected:
            return ThreatLevel.OPPORTUNISTIC

        # Default to noise
        return ThreatLevel.NOISE

    def _extract_iocs(
        self,
        forensic: ForensicReport,
        intel: ThreatIntelReport,
    ) -> List[str]:
        """Extract all Indicators of Compromise."""
        iocs = []

        # From forensic analysis
        iocs.extend(forensic.network_iocs)
        iocs.extend(forensic.file_hashes)

        # From threat intel
        iocs.extend(intel.related_iocs)

        return list(set(iocs))  # Remove duplicates

    def _map_to_mitre_attack(self, forensic: ForensicReport) -> List[str]:
        """Map behaviors to MITRE ATT&CK TTPs."""
        ttps = []

        # Behavior to TTP mapping
        ttp_mapping = {
            'ssh_brute_force': 'T1110.001',
            'sql_injection': 'T1190',
            'command_injection': 'T1059',
            'xss_attack': 'T1189',
            'file_upload': 'T1105',
            'privilege_escalation': 'T1068',
            'lateral_movement': 'T1021',
            'data_exfiltration': 'T1041',
            'persistence': 'T1053',
            'credential_access': 'T1003',
            'discovery': 'T1083',
            'defense_evasion': 'T1070',
        }

        for behavior in forensic.behaviors:
            if behavior in ttp_mapping:
                ttps.append(ttp_mapping[behavior])

        return list(set(ttps))
