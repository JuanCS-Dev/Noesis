"""
Scoring Functions for Forensic Analyzer.

Sophistication scoring, IOC extraction, and confidence calculation.
"""

from __future__ import annotations

import re

from .models import ForensicReport


class ScoringMixin:
    """Mixin providing scoring and IOC extraction capabilities."""

    def _calculate_sophistication_score(self, report: ForensicReport) -> float:
        """
        Calculate attack sophistication score (0-10).

        Factors:
        - Exploit usage (3 points)
        - Custom malware (2 points)
        - Multi-stage attack (2 points)
        - Anti-detection techniques (2 points)
        - Manual operation vs automation (1 point)
        """
        score = 0.0

        if report.exploit_cves:
            score += 3.0

        if report.malware_detected:
            if report.malware_family and 'custom' in report.malware_family.lower():
                score += 2.0
            else:
                score += 1.0

        unique_stages = set(report.attack_stages)
        if len(unique_stages) >= 3:
            score += 2.0
        elif len(unique_stages) >= 2:
            score += 1.0

        anti_detection_behaviors = [
            'obfuscation', 'anti_vm', 'sandbox_evasion',
            'defense_evasion', 'log_deletion'
        ]
        if any(b in report.behaviors for b in anti_detection_behaviors):
            score += 2.0

        if not report.is_automated:
            score += 1.0

        return min(score, 10.0)

    def _extract_iocs(self, report: ForensicReport) -> None:
        """Extract all Indicators of Compromise."""
        if report.source_ip and report.source_ip != 'unknown':
            report.network_iocs.append(f"ip:{report.source_ip}")

        for file_hash in report.file_hashes:
            report.file_iocs.append(f"sha256:{file_hash}")

        for cmd in report.suspicious_commands:
            ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            ips = re.findall(ip_pattern, cmd)
            for ip in ips:
                if ip not in report.network_iocs:
                    report.network_iocs.append(f"ip:{ip}")

            domain_pattern = (
                r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+'
                r'[a-z0-9][a-z0-9-]{0,61}[a-z0-9]\b'
            )
            domains = re.findall(domain_pattern, cmd, re.IGNORECASE)
            for domain in domains:
                if domain not in report.network_iocs:
                    report.network_iocs.append(f"domain:{domain}")

    def _calculate_confidence(self, report: ForensicReport) -> float:
        """Calculate analysis confidence (0-100%)."""
        confidence = 50.0

        confidence += min(len(report.behaviors) * 5, 30)

        if report.file_hashes:
            confidence += 10

        if report.exploit_cves:
            confidence += 10

        return min(confidence, 100.0)
