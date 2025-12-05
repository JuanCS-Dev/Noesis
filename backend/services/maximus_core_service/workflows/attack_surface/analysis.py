"""Analysis Methods for Attack Surface Mapping.

Mixin providing analysis and reporting capabilities.
"""

from __future__ import annotations

from typing import Any

from .models import Finding, RiskLevel


class AnalysisMixin:
    """Mixin providing analysis methods.

    Provides methods for:
    - Risk score calculation
    - Statistics generation
    - Recommendation generation
    """

    def _calculate_risk_score(self, findings: list[Finding]) -> float:
        """Calculate overall risk score.

        Args:
            findings: All findings.

        Returns:
            Risk score (0-100).
        """
        severity_weights = {
            RiskLevel.CRITICAL: 10.0,
            RiskLevel.HIGH: 7.0,
            RiskLevel.MEDIUM: 4.0,
            RiskLevel.LOW: 1.0,
            RiskLevel.INFO: 0.1,
        }

        total_score = sum(severity_weights.get(f.severity, 0) for f in findings)

        max_possible = len(findings) * 10.0 if findings else 1
        risk_score = min(100.0, (total_score / max_possible) * 100.0)

        return round(risk_score, 2)

    def _generate_statistics(self, findings: list[Finding]) -> dict[str, Any]:
        """Generate statistics from findings.

        Args:
            findings: All findings.

        Returns:
            Statistics dictionary.
        """
        stats: dict[str, Any] = {
            "total_findings": len(findings),
            "by_type": {},
            "by_severity": {},
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "info_count": 0,
        }

        for finding in findings:
            ftype = finding.finding_type
            stats["by_type"][ftype] = stats["by_type"].get(ftype, 0) + 1

            severity = finding.severity.value
            stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1

            if finding.severity == RiskLevel.CRITICAL:
                stats["critical_count"] += 1
            elif finding.severity == RiskLevel.HIGH:
                stats["high_count"] += 1
            elif finding.severity == RiskLevel.MEDIUM:
                stats["medium_count"] += 1
            elif finding.severity == RiskLevel.LOW:
                stats["low_count"] += 1
            elif finding.severity == RiskLevel.INFO:
                stats["info_count"] += 1

        return stats

    def _generate_recommendations(
        self,
        findings: list[Finding],
        risk_score: float,
    ) -> list[str]:
        """Generate remediation recommendations.

        Args:
            findings: All findings.
            risk_score: Overall risk score.

        Returns:
            List of recommendations.
        """
        recommendations = []

        # High-level recommendations based on risk score
        if risk_score >= 70:
            recommendations.append(
                "CRITICAL: Immediate remediation required - attack surface highly vulnerable"
            )
        elif risk_score >= 50:
            recommendations.append("HIGH: Prioritize patching identified vulnerabilities")
        elif risk_score >= 30:
            recommendations.append("MEDIUM: Schedule remediation for identified issues")
        else:
            recommendations.append(
                "LOW: Maintain current security posture, monitor for changes"
            )

        # Vulnerability-specific recommendations
        recommendations.extend(self._get_vuln_recommendations(findings))

        # Service-specific recommendations
        recommendations.extend(self._get_service_recommendations(findings))

        # Port exposure recommendations
        recommendations.extend(self._get_port_recommendations(findings))

        # Subdomain recommendations
        recommendations.extend(self._get_subdomain_recommendations(findings))

        return recommendations

    def _get_vuln_recommendations(self, findings: list[Finding]) -> list[str]:
        """Get vulnerability-specific recommendations.

        Args:
            findings: All findings.

        Returns:
            List of vulnerability recommendations.
        """
        recommendations = []
        vuln_findings = [f for f in findings if f.finding_type == "vulnerability"]

        if vuln_findings:
            high_severity = [
                f
                for f in vuln_findings
                if f.severity in [RiskLevel.CRITICAL, RiskLevel.HIGH]
            ]
            if high_severity:
                recommendations.append(
                    f"Patch {len(high_severity)} high/critical vulnerabilities immediately"
                )

            exploitable = [
                f for f in vuln_findings if f.details.get("exploit_available")
            ]
            if exploitable:
                recommendations.append(
                    f"URGENT: {len(exploitable)} vulnerabilities have public exploits available"
                )

        return recommendations

    def _get_service_recommendations(self, findings: list[Finding]) -> list[str]:
        """Get service-specific recommendations.

        Args:
            findings: All findings.

        Returns:
            List of service recommendations.
        """
        recommendations = []
        service_findings = [f for f in findings if f.finding_type == "service"]

        outdated_services = [
            f
            for f in service_findings
            if "nginx" in f.details.get("service", "").lower()
        ]
        if outdated_services:
            recommendations.append("Update web servers to latest stable versions")

        return recommendations

    def _get_port_recommendations(self, findings: list[Finding]) -> list[str]:
        """Get port exposure recommendations.

        Args:
            findings: All findings.

        Returns:
            List of port recommendations.
        """
        recommendations = []
        port_findings = [f for f in findings if f.finding_type == "open_port"]

        sensitive_ports = [
            f for f in port_findings if f.details.get("port") in [21, 23, 3389]
        ]
        if sensitive_ports:
            recommendations.append(
                f"Close {len(sensitive_ports)} sensitive ports or restrict access"
            )

        return recommendations

    def _get_subdomain_recommendations(self, findings: list[Finding]) -> list[str]:
        """Get subdomain recommendations.

        Args:
            findings: All findings.

        Returns:
            List of subdomain recommendations.
        """
        recommendations = []
        subdomain_findings = [f for f in findings if f.finding_type == "subdomain"]

        if len(subdomain_findings) > 10:
            recommendations.append(
                "Review subdomain inventory - reduce attack surface by "
                "decommissioning unused domains"
            )

        return recommendations
