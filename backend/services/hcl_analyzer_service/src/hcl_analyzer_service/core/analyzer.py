"""
HCL Analyzer Service - Core Logic
=================================

Core analysis logic for system metrics.
"""

from __future__ import annotations

from typing import Any, Dict, List

from hcl_analyzer_service.config import AnalyzerSettings
from hcl_analyzer_service.models.analysis import (
    AnalysisResult,
    Anomaly,
    AnomalyType,
    SystemMetrics,
)
from hcl_analyzer_service.utils.logging_config import get_logger

logger = get_logger(__name__)


def detect_static_anomalies(metrics: SystemMetrics) -> List[Anomaly]:
    """
    Detect anomalies based on static thresholds.

    This is a standalone function that can be reused by both
    SystemAnalyzer and MLSystemAnalyzer.

    Args:
        metrics: System metrics to analyze

    Returns:
        List of detected anomalies
    """
    anomalies: List[Anomaly] = []

    # CPU Usage Analysis
    if metrics.cpu_usage > 90.0:
        anomalies.append(
            Anomaly(
                type=AnomalyType.SPIKE,
                metric_name="cpu_usage",
                current_value=metrics.cpu_usage,
                severity=0.9,
                description="Critical CPU usage detected (>90%)",
            )
        )
    elif metrics.cpu_usage > 75.0:
        anomalies.append(
            Anomaly(
                type=AnomalyType.SPIKE,
                metric_name="cpu_usage",
                current_value=metrics.cpu_usage,
                severity=0.6,
                description="High CPU usage detected (>75%)",
            )
        )

    # Memory Usage Analysis
    if metrics.memory_usage > 90.0:
        anomalies.append(
            Anomaly(
                type=AnomalyType.SPIKE,
                metric_name="memory_usage",
                current_value=metrics.memory_usage,
                severity=0.9,
                description="Critical memory usage detected (>90%)",
            )
        )

    # Error Rate Analysis
    if metrics.error_rate > 0.05:
        anomalies.append(
            Anomaly(
                type=AnomalyType.SPIKE,
                metric_name="error_rate",
                current_value=metrics.error_rate,
                severity=1.0,
                description="High system error rate detected (>5%)",
            )
        )

    return anomalies


def generate_anomaly_recommendations(anomalies: List[Anomaly]) -> List[str]:
    """
    Generate actionable recommendations based on detected anomalies.

    Args:
        anomalies: List of detected anomalies

    Returns:
        List of recommendation strings
    """
    recommendations: List[str] = []

    for anomaly in anomalies:
        if anomaly.metric_name == "cpu_usage":
            recommendations.append("Scale up CPU resources or optimize workload.")
        elif anomaly.metric_name == "memory_usage":
            recommendations.append("Check for memory leaks or increase memory limits.")
        elif anomaly.metric_name == "error_rate":
            recommendations.append("Investigate logs for recent error spikes.")

    if not recommendations:
        recommendations.append("System is healthy. No actions required.")

    return recommendations


class SystemAnalyzer:  # pylint: disable=too-few-public-methods
    """
    Analyzes system metrics to detect anomalies and assess health.
    """

    def __init__(self, settings: AnalyzerSettings):
        """
        Initialize the analyzer.

        Args:
            settings: Analyzer settings
        """
        self.settings = settings

    async def analyze_metrics(self, metrics: SystemMetrics) -> AnalysisResult:
        """
        Analyze the provided system metrics.

        Args:
            metrics: System metrics snapshot

        Returns:
            Comprehensive analysis result
        """
        logger.info("analyzing_metrics", timestamp=metrics.timestamp)

        anomalies = self._detect_anomalies(metrics)
        health_score = self._calculate_health_score(metrics, anomalies)
        trends = self._identify_trends(metrics)
        recommendations = self._generate_recommendations(anomalies)
        requires_intervention = health_score < self.settings.anomaly_threshold

        result = AnalysisResult(
            overall_health_score=health_score,
            anomalies=anomalies,
            trends=trends,
            recommendations=recommendations,
            requires_intervention=requires_intervention,
        )

        logger.info(
            "analysis_complete",
            health_score=health_score,
            anomalies_count=len(anomalies),
            requires_intervention=requires_intervention,
        )

        return result

    def _detect_anomalies(self, metrics: SystemMetrics) -> List[Anomaly]:
        """Detect anomalies based on static thresholds."""
        return detect_static_anomalies(metrics)

    def _calculate_health_score(
        self, metrics: SystemMetrics, anomalies: List[Anomaly]
    ) -> float:
        """Calculate overall system health score (0.0 to 1.0)."""
        base_score = 1.0

        # Penalize for anomalies
        for anomaly in anomalies:
            base_score -= (anomaly.severity * 0.1)

        # Penalize for high latency
        if metrics.avg_latency_ms > 500:
            base_score -= 0.1

        # Ensure score is within bounds
        return max(0.0, min(1.0, base_score))

    def _identify_trends(self, metrics: SystemMetrics) -> Dict[str, Any]:
        """
        Identify trends based on current metrics snapshot.

        Note:
            This basic implementation only detects latency degradation.
            For historical trend analysis, use MLSystemAnalyzer which
            maintains metrics history for proper trend detection.
        """
        return {
            "cpu_trend": "stable",
            "memory_trend": "stable",
            "latency_trend": "stable" if metrics.avg_latency_ms < 200 else "degrading"
        }

    def _generate_recommendations(self, anomalies: List[Anomaly]) -> List[str]:
        """Generate actionable recommendations based on anomalies."""
        return generate_anomaly_recommendations(anomalies)

    def get_status(self) -> Dict[str, str]:
        """Get analyzer status."""
        return {"status": "active", "threshold": str(self.settings.anomaly_threshold)}
