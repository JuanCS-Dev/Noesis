"""Compliance Reporter Module.

Generates compliance reports and recommendations.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from ..base import (
    ConstitutionalViolation,
    GuardianAgent,
    GuardianIntervention,
    GuardianPriority,
    VetoAction,
)
from .models import CoordinatorMetrics

logger = logging.getLogger(__name__)


class ComplianceReporter:
    """Generates compliance reports and recommendations.

    Aggregates data from all Guardians and produces unified
    compliance reports with actionable recommendations.

    Attributes:
        metrics: Coordinator metrics.
        guardians: Dictionary of Guardian agents.
    """

    def __init__(
        self,
        metrics: CoordinatorMetrics,
        guardians: dict[str, GuardianAgent],
    ) -> None:
        """Initialize compliance reporter.

        Args:
            metrics: Coordinator metrics instance.
            guardians: Dictionary of Guardian agents.
        """
        self.metrics = metrics
        self.guardians = guardians

    def generate_compliance_report(
        self,
        violations: list[ConstitutionalViolation],
        interventions: list[GuardianIntervention],
        vetos: list[VetoAction],
        period_hours: int = 24,
    ) -> dict[str, Any]:
        """Generate unified compliance report.

        Args:
            violations: All violations.
            interventions: All interventions.
            vetos: All vetos.
            period_hours: Report period in hours.

        Returns:
            Complete compliance report dictionary.
        """
        period_start = datetime.utcnow() - timedelta(hours=period_hours)

        guardian_reports = {}
        for name, guardian in self.guardians.items():
            guardian_reports[name] = guardian.generate_report(period_hours).to_dict()

        period_violations = [
            v for v in violations if v.detected_at > period_start
        ]
        period_interventions = [
            i for i in interventions if i.timestamp > period_start
        ]
        period_vetos = [
            v for v in vetos if v.enacted_at > period_start
        ]

        critical_count = len([
            v for v in period_violations
            if v.severity == GuardianPriority.CRITICAL
        ])

        return {
            "report_id": f"compliance_{datetime.utcnow().timestamp()}",
            "period_start": period_start.isoformat(),
            "period_end": datetime.utcnow().isoformat(),
            "coordinator_metrics": self.metrics.to_dict(),
            "guardian_reports": guardian_reports,
            "summary": {
                "total_violations": len(period_violations),
                "total_interventions": len(period_interventions),
                "total_vetos": len(period_vetos),
                "compliance_score": self.metrics.compliance_score,
                "critical_violations": critical_count,
            },
            "top_violations": self._get_top_violations(period_violations),
            "recommendations": self._generate_recommendations(period_violations),
        }

    def _get_top_violations(
        self,
        violations: list[ConstitutionalViolation],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get top violations by frequency.

        Args:
            violations: List of violations.
            limit: Maximum number of violations to return.

        Returns:
            List of top violations with counts.
        """
        violation_counts: dict[str, int] = defaultdict(int)

        for v in violations:
            key = f"{v.article.value}:{v.rule}"
            violation_counts[key] += 1

        sorted_violations = sorted(
            violation_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        return [
            {"violation": k, "count": v}
            for k, v in sorted_violations[:limit]
        ]

    def _generate_recommendations(
        self,
        violations: list[ConstitutionalViolation],
    ) -> list[str]:
        """Generate recommendations based on violations.

        Args:
            violations: List of violations to analyze.

        Returns:
            List of actionable recommendations.
        """
        recommendations = []

        quality_violations = [
            v for v in violations if v.article.value == "ARTICLE_II"
        ]
        if len(quality_violations) > 10:
            recommendations.append(
                "High number of quality violations. "
                "Implement code review and testing requirements."
            )

        security_violations = [
            v for v in violations if v.article.value == "ARTICLE_III"
        ]
        if len(security_violations) > 5:
            recommendations.append(
                "Multiple Zero Trust violations. "
                "Conduct security audit and implement authentication."
            )

        resilience_violations = [
            v for v in violations if v.article.value == "ARTICLE_IV"
        ]
        if len(resilience_violations) > 5:
            recommendations.append(
                "System lacks antifragility. "
                "Implement chaos engineering and resilience patterns."
            )

        governance_violations = [
            v for v in violations if v.article.value == "ARTICLE_V"
        ]
        if len(governance_violations) > 3:
            recommendations.append(
                "Governance violations detected. "
                "Review Prior Legislation principle and implement controls."
            )

        if not recommendations:
            recommendations.append(
                "System is generally compliant. "
                "Continue monitoring and improvement."
            )

        return recommendations

    def get_violation_summary_by_article(
        self,
        violations: list[ConstitutionalViolation],
    ) -> dict[str, dict[str, int]]:
        """Get violation summary grouped by article.

        Args:
            violations: List of violations.

        Returns:
            Dictionary with article -> severity counts.
        """
        summary: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

        for v in violations:
            article = v.article.value
            severity = v.severity.value
            summary[article][severity] += 1
            summary[article]["total"] += 1

        return {k: dict(v) for k, v in summary.items()}

    def get_trend_analysis(
        self,
        violations: list[ConstitutionalViolation],
        hours: int = 24,
        interval_hours: int = 1,
    ) -> list[dict[str, Any]]:
        """Get violation trend over time.

        Args:
            violations: List of violations.
            hours: Total period to analyze.
            interval_hours: Interval for each data point.

        Returns:
            List of trend data points.
        """
        trend_data = []
        now = datetime.utcnow()

        for i in range(hours // interval_hours):
            interval_start = now - timedelta(hours=(i + 1) * interval_hours)
            interval_end = now - timedelta(hours=i * interval_hours)

            interval_violations = [
                v for v in violations
                if interval_start <= v.detected_at < interval_end
            ]

            trend_data.append({
                "interval_start": interval_start.isoformat(),
                "interval_end": interval_end.isoformat(),
                "violation_count": len(interval_violations),
                "critical_count": len([
                    v for v in interval_violations
                    if v.severity == GuardianPriority.CRITICAL
                ]),
            })

        trend_data.reverse()
        return trend_data
