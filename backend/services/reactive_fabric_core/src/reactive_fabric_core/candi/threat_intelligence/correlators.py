"""
Correlators for Threat Intelligence.

IOC, tool, exploit, and campaign correlation.
"""

from __future__ import annotations

from typing import Any, Dict

from ..forensic_analyzer import ForensicReport
from .models import ThreatIntelReport


class CorrelatorMixin:
    """Mixin providing correlation capabilities."""

    ioc_database: Dict[str, Dict[str, Any]]
    tool_database: Dict[str, Dict[str, Any]]
    exploit_database: Dict[str, Dict[str, Any]]
    campaign_database: Dict[str, Dict[str, Any]]

    async def _correlate_iocs(
        self,
        forensic: ForensicReport,
        report: ThreatIntelReport,
    ) -> None:
        """Correlate IOCs against threat intelligence."""
        # Check all network IOCs
        for ioc in forensic.network_iocs:
            if ioc in self.ioc_database:
                report.known_iocs.append(ioc)
                intel = self.ioc_database[ioc]

                # Add reputation
                report.ioc_reputation[ioc] = intel.get('reputation', 'unknown')

                # Add threat tags
                for tag in intel.get('tags', []):
                    if tag not in report.threat_tags:
                        report.threat_tags.append(tag)

                # Track first/last seen
                if 'first_seen' in intel:
                    fs = intel['first_seen']
                    if not report.first_seen or fs < report.first_seen:
                        report.first_seen = fs

                if 'last_seen' in intel:
                    ls = intel['last_seen']
                    if not report.last_seen or ls > report.last_seen:
                        report.last_seen = ls

        # Check file hashes
        for file_hash in forensic.file_hashes:
            ioc_key = f"sha256:{file_hash}"
            if ioc_key in self.ioc_database:
                report.known_iocs.append(ioc_key)
                intel = self.ioc_database[ioc_key]
                report.ioc_reputation[ioc_key] = intel.get('reputation', 'unknown')

    async def _correlate_tools(
        self,
        forensic: ForensicReport,
        report: ThreatIntelReport,
    ) -> None:
        """Correlate tools and malware families."""
        # Check malware family
        if forensic.malware_family:
            malware_lower = forensic.malware_family.lower()
            if malware_lower in self.tool_database:
                report.known_tools.append(forensic.malware_family)
                tool_intel = self.tool_database[malware_lower]

                # Add threat tags
                for tag in tool_intel.get('tags', []):
                    if tag not in report.threat_tags:
                        report.threat_tags.append(tag)

        # Check for known tools in commands
        for cmd in forensic.suspicious_commands:
            cmd_lower = cmd.lower()
            for tool_name, tool_info in self.tool_database.items():
                if tool_name in cmd_lower:
                    if tool_name not in report.known_tools:
                        report.known_tools.append(tool_name)

                    for tag in tool_info.get('tags', []):
                        if tag not in report.threat_tags:
                            report.threat_tags.append(tag)

    async def _correlate_exploits(
        self,
        forensic: ForensicReport,
        report: ThreatIntelReport,
    ) -> None:
        """Correlate exploits with CVE database."""
        for cve in forensic.exploit_cves:
            if cve in self.exploit_database:
                report.known_exploits.append(cve)
                exploit_intel = self.exploit_database[cve]

                # Add threat tags
                for tag in exploit_intel.get('tags', []):
                    if tag not in report.threat_tags:
                        report.threat_tags.append(tag)

    async def _correlate_campaigns(
        self,
        forensic: ForensicReport,
        report: ThreatIntelReport,
    ) -> None:
        """Correlate with known threat campaigns."""
        # Check behaviors against campaign signatures
        observed_behaviors = set(forensic.behaviors)

        for campaign_name, campaign_info in self.campaign_database.items():
            campaign_behaviors = set(campaign_info.get('behaviors', []))

            # Check for overlap
            overlap = observed_behaviors & campaign_behaviors
            if len(overlap) >= 2:  # At least 2 matching behaviors
                report.related_campaigns.append(campaign_name)

                # Add campaign tags
                for tag in campaign_info.get('tags', []):
                    if tag not in report.threat_tags:
                        report.threat_tags.append(tag)

    async def _enrich_iocs(self, report: ThreatIntelReport) -> None:
        """Enrich IOCs with related indicators."""
        for ioc in report.known_iocs:
            if ioc in self.ioc_database:
                intel = self.ioc_database[ioc]
                related = intel.get('related_iocs', [])

                for related_ioc in related:
                    if related_ioc not in report.related_iocs:
                        report.related_iocs.append(related_ioc)
