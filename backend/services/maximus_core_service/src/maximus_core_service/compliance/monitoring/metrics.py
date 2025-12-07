"""Compliance Monitoring Metrics.

Mixin providing metrics calculation functionality.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from ..base import ViolationSeverity
from ..compliance_engine import ComplianceSnapshot
from ..evidence_collector import EvidenceCollector
from .models import MonitoringMetrics


class MetricsMixin:
    """Mixin providing metrics calculation methods.

    Handles metrics calculation, history, and trend analysis.

    Attributes:
        evidence_collector: Evidence collector instance.
        _metrics_history: List of metrics snapshots.
    """

    evidence_collector: EvidenceCollector | None
    _metrics_history: list[MonitoringMetrics]

    def _calculate_metrics(self, snapshot: ComplianceSnapshot) -> MonitoringMetrics:
        """Calculate monitoring metrics from snapshot.

        Args:
            snapshot: Compliance snapshot.

        Returns:
            Monitoring metrics.
        """
        violation_counts = self._count_violations_by_severity(snapshot)
        evidence_metrics = self._calculate_evidence_metrics()
        trend = self._calculate_trend()

        return MonitoringMetrics(
            overall_compliance_percentage=snapshot.overall_compliance_percentage,
            overall_score=snapshot.overall_score,
            compliance_by_regulation={
                reg_type.value: result.compliance_percentage
                for reg_type, result in snapshot.regulation_results.items()
            },
            total_violations=snapshot.total_violations,
            critical_violations=violation_counts["critical"],
            high_violations=violation_counts["high"],
            medium_violations=violation_counts["medium"],
            low_violations=violation_counts["low"],
            total_evidence=evidence_metrics["total"],
            expired_evidence=evidence_metrics["expired"],
            expiring_soon_evidence=evidence_metrics["expiring_soon"],
            compliance_trend=trend,
        )

    def _count_violations_by_severity(
        self,
        snapshot: ComplianceSnapshot,
    ) -> dict[str, int]:
        """Count violations by severity level.

        Args:
            snapshot: Compliance snapshot.

        Returns:
            Dict with violation counts.
        """
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for result in snapshot.regulation_results.values():
            for violation in result.violations:
                if violation.severity == ViolationSeverity.CRITICAL:
                    counts["critical"] += 1
                elif violation.severity == ViolationSeverity.HIGH:
                    counts["high"] += 1
                elif violation.severity == ViolationSeverity.MEDIUM:
                    counts["medium"] += 1
                elif violation.severity == ViolationSeverity.LOW:
                    counts["low"] += 1

        return counts

    def _calculate_evidence_metrics(self) -> dict[str, int]:
        """Calculate evidence-related metrics.

        Returns:
            Dict with evidence metrics.
        """
        metrics = {"total": 0, "expired": 0, "expiring_soon": 0}

        if not self.evidence_collector:
            return metrics

        all_evidence = self.evidence_collector.get_all_evidence()
        threshold_date = datetime.utcnow() + timedelta(days=30)

        for evidence_list in all_evidence.values():
            metrics["total"] += len(evidence_list)
            for evidence in evidence_list:
                if evidence.is_expired():
                    metrics["expired"] += 1
                elif (
                    evidence.expiration_date
                    and evidence.expiration_date < threshold_date
                ):
                    metrics["expiring_soon"] += 1

        return metrics

    def _calculate_trend(self) -> str:
        """Calculate compliance trend based on metrics history.

        Returns:
            Trend: improving, stable, declining.
        """
        if len(self._metrics_history) < 2:
            return "stable"

        latest = self._metrics_history[-1]
        week_ago = self._get_week_ago_metric()

        if not week_ago:
            week_ago = self._metrics_history[-2]

        diff = (
            latest.overall_compliance_percentage - week_ago.overall_compliance_percentage
        )

        if diff > 2.0:
            return "improving"
        if diff < -2.0:
            return "declining"
        return "stable"

    def _get_week_ago_metric(self) -> MonitoringMetrics | None:
        """Get metric from approximately one week ago.

        Returns:
            Metric from week ago or None.
        """
        cutoff = datetime.utcnow() - timedelta(days=7)
        for metric in reversed(self._metrics_history[:-1]):
            if metric.timestamp < cutoff:
                return metric
        return None

    def get_current_metrics(self) -> MonitoringMetrics | None:
        """Get current monitoring metrics.

        Returns:
            Latest metrics or None.
        """
        if not self._metrics_history:
            return None
        return self._metrics_history[-1]

    def get_metrics_history(self, days: int = 30) -> list[MonitoringMetrics]:
        """Get metrics history for specified days.

        Args:
            days: Number of days of history.

        Returns:
            List of metrics.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        return [m for m in self._metrics_history if m.timestamp > cutoff]

    def generate_dashboard_data(self) -> dict[str, Any]:
        """Generate dashboard data for compliance monitoring.

        Returns:
            Dashboard data dict.
        """
        current_metrics = self.get_current_metrics()

        if not current_metrics:
            return {"error": "No metrics available"}

        recent_alerts = sorted(
            getattr(self, "_alerts", []),
            key=lambda a: a.triggered_at,
            reverse=True,
        )[:10]

        return {
            "current_metrics": {
                "overall_compliance": current_metrics.overall_compliance_percentage,
                "overall_score": current_metrics.overall_score,
                "trend": current_metrics.compliance_trend,
                "total_violations": current_metrics.total_violations,
                "critical_violations": current_metrics.critical_violations,
            },
            "compliance_by_regulation": current_metrics.compliance_by_regulation,
            "violations_by_severity": {
                "critical": current_metrics.critical_violations,
                "high": current_metrics.high_violations,
                "medium": current_metrics.medium_violations,
                "low": current_metrics.low_violations,
            },
            "evidence_health": {
                "total": current_metrics.total_evidence,
                "expired": current_metrics.expired_evidence,
                "expiring_soon": current_metrics.expiring_soon_evidence,
            },
            "recent_alerts": [
                {
                    "alert_id": alert.alert_id,
                    "type": alert.alert_type,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "triggered_at": alert.triggered_at.isoformat(),
                    "acknowledged": alert.acknowledged,
                }
                for alert in recent_alerts
            ],
        }
