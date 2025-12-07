"""Credential Analysis Methods.

Scoring, statistics, and recommendations.
"""

from __future__ import annotations

from typing import Any

from .models import CredentialFinding, CredentialRiskLevel


class AnalysisMixin:
    """Mixin providing analysis methods."""

    def _calculate_exposure_score(
        self, findings: list[CredentialFinding], breach_count: int
    ) -> float:
        """Calculate credential exposure score."""
        severity_weights = {
            CredentialRiskLevel.CRITICAL: 25.0,
            CredentialRiskLevel.HIGH: 15.0,
            CredentialRiskLevel.MEDIUM: 8.0,
            CredentialRiskLevel.LOW: 2.0,
            CredentialRiskLevel.INFO: 0.5,
        }

        total_score = sum(
            severity_weights.get(f.severity, 0) for f in findings
        )

        breach_multiplier = min(2.0, 1.0 + (breach_count * 0.2))
        total_score *= breach_multiplier

        darkweb_findings = [f for f in findings if f.finding_type == "darkweb"]
        if darkweb_findings:
            total_score += 15.0

        username_findings = [
            f
            for f in findings
            if f.finding_type == "username" and f.details.get("found")
        ]
        platform_bonus = min(10.0, len(username_findings) * 0.5)
        total_score += platform_bonus

        exposure_score = min(100.0, total_score)

        return round(exposure_score, 2)

    def _generate_statistics(
        self, findings: list[CredentialFinding], breach_count: int
    ) -> dict[str, Any]:
        """Generate statistics from findings."""
        stats: dict[str, Any] = {
            "total_findings": len(findings),
            "breach_count": breach_count,
            "by_type": {},
            "by_severity": {},
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "info_count": 0,
            "platforms_found": 0,
            "darkweb_mentions": 0,
            "dorking_results": 0,
        }

        for finding in findings:
            ftype = finding.finding_type
            stats["by_type"][ftype] = stats["by_type"].get(ftype, 0) + 1

            severity = finding.severity.value
            stats["by_severity"][severity] = (
                stats["by_severity"].get(severity, 0) + 1
            )

            if finding.severity == CredentialRiskLevel.CRITICAL:
                stats["critical_count"] += 1
            elif finding.severity == CredentialRiskLevel.HIGH:
                stats["high_count"] += 1
            elif finding.severity == CredentialRiskLevel.MEDIUM:
                stats["medium_count"] += 1
            elif finding.severity == CredentialRiskLevel.LOW:
                stats["low_count"] += 1
            elif finding.severity == CredentialRiskLevel.INFO:
                stats["info_count"] += 1

            if finding.finding_type == "username" and finding.details.get("found"):
                stats["platforms_found"] += 1
            if finding.finding_type == "darkweb":
                stats["darkweb_mentions"] += 1
            if finding.finding_type == "dork":
                stats["dorking_results"] += 1

        return stats

    def _generate_recommendations(
        self, findings: list[CredentialFinding], exposure_score: float
    ) -> list[str]:
        """Generate security recommendations."""
        recommendations = []

        if exposure_score >= 70:
            recommendations.append(
                "CRITICAL: Immediate action required - credentials are highly exposed"
            )
            recommendations.append(
                "Change ALL passwords immediately using a password manager"
            )
            recommendations.append(
                "Enable multi-factor authentication (MFA) on all accounts"
            )
        elif exposure_score >= 50:
            recommendations.append("HIGH: Significant credential exposure detected")
            recommendations.append("Change passwords for breached accounts")
            recommendations.append("Enable MFA where available")
        elif exposure_score >= 30:
            recommendations.append("MEDIUM: Moderate credential exposure detected")
            recommendations.append("Review and update passwords for affected accounts")
        else:
            recommendations.append("LOW: Limited credential exposure detected")
            recommendations.append("Continue monitoring for new breaches")

        breach_findings = [f for f in findings if f.finding_type == "breach"]
        if breach_findings:
            password_breaches = [
                f
                for f in breach_findings
                if f.severity == CredentialRiskLevel.CRITICAL
            ]
            if password_breaches:
                recommendations.append(
                    f"URGENT: Passwords exposed in {len(password_breaches)} "
                    "breaches - change immediately"
                )

            verified_breaches = [
                f for f in breach_findings if f.details.get("is_verified")
            ]
            if verified_breaches:
                recommendations.append(
                    f"{len(verified_breaches)} verified breaches - "
                    "prioritize these accounts"
                )

        darkweb_findings = [f for f in findings if f.finding_type == "darkweb"]
        if darkweb_findings:
            onion_findings = [
                f for f in darkweb_findings if f.details.get("onion_service")
            ]
            if onion_findings:
                recommendations.append(
                    f"CRITICAL: Credentials found on {len(onion_findings)} "
                    "Tor marketplaces"
                )
            recommendations.append("Monitor dark web continuously for new mentions")

        dork_findings = [f for f in findings if f.finding_type == "dork"]
        if dork_findings:
            github_findings = [
                f for f in dork_findings if "github.com" in f.details.get("url", "")
            ]
            if github_findings:
                recommendations.append(
                    "Remove exposed credentials from GitHub repositories"
                )
            pastebin_findings = [
                f
                for f in dork_findings
                if "pastebin" in f.details.get("url", "").lower()
            ]
            if pastebin_findings:
                recommendations.append(
                    "Contact Pastebin to remove exposed credential posts"
                )

        username_findings = [
            f
            for f in findings
            if f.finding_type == "username" and f.details.get("found")
        ]
        if len(username_findings) > 10:
            recommendations.append(
                f"Username found on {len(username_findings)} platforms - "
                "review account security on each"
            )

        recommendations.append(
            "Use unique passwords for each account (password manager recommended)"
        )
        recommendations.append(
            "Enable breach monitoring alerts (e.g., HIBP notifications)"
        )
        recommendations.append(
            "Review and remove unused accounts to reduce attack surface"
        )

        return recommendations
