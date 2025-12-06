"""
HCL ML Analyzer - Machine Learning Enhanced Analysis
====================================================

Enhanced system analyzer using SARIMA + Isolation Forest hybrid detection.
Replaces static threshold-based detection with adaptive ML-based detection.

Architecture:
1. HybridAnomalyDetector for anomaly detection
2. Automatic model training from historical data
3. Online learning for continuous adaptation
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from hcl_analyzer_service.config import AnalyzerSettings
from hcl_analyzer_service.models.analysis import (
    AnalysisResult,
    Anomaly,
    AnomalyType,
    SystemMetrics,
)
from hcl_analyzer_service.core.analyzer import detect_static_anomalies, generate_anomaly_recommendations
from hcl_analyzer_service.core.models.hybrid_detector import (
    HybridAnomalyDetector,
    HybridConfig,
    HybridAnomalyResult,
    AnomalySource,
)
from hcl_analyzer_service.utils.logging_config import get_logger

logger = get_logger(__name__)


class MLSystemAnalyzer:
    """
    Machine Learning enhanced system analyzer.

    Uses Hybrid Anomaly Detector (SARIMA + Isolation Forest) for:
    - Temporal anomaly detection (SARIMA)
    - Multivariate anomaly detection (Isolation Forest)
    - Adaptive thresholds based on historical data

    Example:
        >>> analyzer = MLSystemAnalyzer(settings)
        >>> analyzer.train(historical_metrics)
        >>> result = await analyzer.analyze_metrics(current_metrics)
    """

    # Feature names for ML models
    FEATURE_NAMES = [
        "cpu_usage",
        "memory_usage",
        "disk_io_rate",
        "network_io_rate",
        "avg_latency_ms",
        "error_rate",
    ]

    def __init__(
        self,
        settings: AnalyzerSettings,
        hybrid_config: Optional[HybridConfig] = None,
    ):
        """
        Initialize ML analyzer.

        Args:
            settings: Analyzer settings
            hybrid_config: Optional hybrid detector configuration
        """
        self.settings = settings

        # Configure hybrid detector
        config = hybrid_config or HybridConfig(
            sarima_weight=0.4,
            isolation_weight=0.6,
            sarima_sigma_threshold=2.5,
            isolation_score_threshold=-0.3,
            ensemble_threshold=0.5,
            feature_names=self.FEATURE_NAMES,
            sarima_feature_index=0,  # CPU usage for time series
        )

        self._detector = HybridAnomalyDetector(config)
        self._trained = False
        self._metrics_history: List[SystemMetrics] = []

        logger.info(
            "ml_analyzer_initialized",
            analyzer_type="hybrid_sarima_isolation",
        )

    def train(
        self,
        historical_metrics: List[SystemMetrics],
        target_metric: str = "cpu_usage",
    ) -> bool:
        """
        Train ML models on historical data.

        Args:
            historical_metrics: Historical metrics for training
            target_metric: Which metric to use for SARIMA (default: cpu_usage)

        Returns:
            True if training succeeded
        """
        if len(historical_metrics) < 50:
            logger.warning(
                "insufficient_training_data",
                count=len(historical_metrics),
                min_required=50,
            )
            return False

        # Extract time series for SARIMA
        time_series = [getattr(m, target_metric) for m in historical_metrics]

        # Extract feature vectors for Isolation Forest
        multivariate_data = [
            self._extract_features(m) for m in historical_metrics
        ]

        # Train hybrid detector
        result = self._detector.fit(time_series, multivariate_data)

        self._trained = result
        self._metrics_history = list(historical_metrics)

        logger.info(
            "ml_analyzer_trained",
            data_points=len(historical_metrics),
            success=result,
        )

        return result

    def _extract_features(self, metrics: SystemMetrics) -> List[float]:
        """Extract feature vector from metrics."""
        return [
            metrics.cpu_usage,
            metrics.memory_usage,
            metrics.disk_io_rate,
            metrics.network_io_rate,
            metrics.avg_latency_ms,
            metrics.error_rate,
        ]

    async def analyze_metrics(self, metrics: SystemMetrics) -> AnalysisResult:
        """
        Analyze system metrics using ML-based detection.

        Args:
            metrics: Current system metrics

        Returns:
            Analysis result with anomalies and recommendations
        """
        logger.info("analyzing_metrics_ml", timestamp=metrics.timestamp)

        # Get ML-based anomaly detection
        if self._trained:
            ml_result = self._detector.detect_and_update(
                time_series_value=metrics.cpu_usage,
                feature_vector=self._extract_features(metrics),
            )
            anomalies = self._convert_ml_anomalies(ml_result, metrics)
        else:
            # Fallback to static thresholds if not trained
            anomalies = self._detect_anomalies_static(metrics)
            ml_result = None

        # Calculate health score
        health_score = self._calculate_health_score(metrics, anomalies, ml_result)

        # Identify trends
        trends = self._identify_trends(metrics)

        # Generate recommendations
        recommendations = self._generate_recommendations(anomalies, ml_result)

        requires_intervention = health_score < self.settings.anomaly_threshold

        result = AnalysisResult(
            overall_health_score=health_score,
            anomalies=anomalies,
            trends=trends,
            recommendations=recommendations,
            requires_intervention=requires_intervention,
        )

        logger.info(
            "ml_analysis_complete",
            health_score=health_score,
            anomalies_count=len(anomalies),
            ml_detected=ml_result.is_anomaly if ml_result else None,
            requires_intervention=requires_intervention,
        )

        # Store for history
        self._metrics_history.append(metrics)
        if len(self._metrics_history) > 10000:
            self._metrics_history = self._metrics_history[-10000:]

        return result

    def _convert_ml_anomalies(
        self,
        ml_result: HybridAnomalyResult,
        metrics: SystemMetrics,
    ) -> List[Anomaly]:
        """Convert ML detection result to Anomaly list."""
        anomalies: List[Anomaly] = []

        if not ml_result.is_anomaly:
            return anomalies

        # Determine anomaly type based on source
        if ml_result.source == AnomalySource.SARIMA:
            anomaly_type = AnomalyType.TREND
            description = f"Temporal anomaly: {ml_result.explanation}"
        elif ml_result.source == AnomalySource.ISOLATION:
            anomaly_type = AnomalyType.OUTLIER
            description = f"Multivariate anomaly: {ml_result.explanation}"
        elif ml_result.source == AnomalySource.BOTH:
            anomaly_type = AnomalyType.SPIKE
            description = f"CRITICAL: {ml_result.explanation}"
        else:
            return anomalies

        # Severity based on weighted score
        severity = min(1.0, ml_result.weighted_score)

        # Create anomaly for most contributing feature
        if ml_result.feature_contributions:
            sorted_features = sorted(
                ml_result.feature_contributions.items(),
                key=lambda x: abs(x[1]),
                reverse=True,
            )
            top_feature = sorted_features[0][0]
            current_value = getattr(metrics, top_feature, 0)
        else:
            top_feature = "cpu_usage"
            current_value = metrics.cpu_usage

        anomalies.append(
            Anomaly(
                type=anomaly_type,
                metric_name=top_feature,
                current_value=current_value,
                severity=severity,
                description=description,
            )
        )

        return anomalies

    def _detect_anomalies_static(self, metrics: SystemMetrics) -> List[Anomaly]:
        """Fallback static threshold detection."""
        return detect_static_anomalies(metrics)

    def _calculate_health_score(
        self,
        metrics: SystemMetrics,
        anomalies: List[Anomaly],
        ml_result: Optional[HybridAnomalyResult],
    ) -> float:
        """Calculate health score combining ML and heuristics."""
        base_score = 1.0

        # ML-based penalty
        if ml_result and ml_result.is_anomaly:
            base_score -= ml_result.weighted_score * 0.4

        # Anomaly-based penalty
        for anomaly in anomalies:
            base_score -= anomaly.severity * 0.1

        # Latency penalty
        if metrics.avg_latency_ms > 500:
            base_score -= 0.1

        return max(0.0, min(1.0, base_score))

    def _identify_trends(self, metrics: SystemMetrics) -> Dict[str, Any]:
        """Identify trends from metrics history."""
        trends = {
            "cpu_trend": "stable",
            "memory_trend": "stable",
            "latency_trend": "stable" if metrics.avg_latency_ms < 200 else "degrading",
        }

        # Calculate trends if we have history
        if len(self._metrics_history) >= 10:
            recent = self._metrics_history[-10:]

            # CPU trend
            cpu_values = [m.cpu_usage for m in recent]
            cpu_trend = cpu_values[-1] - cpu_values[0]
            if cpu_trend > 10:
                trends["cpu_trend"] = "increasing"
            elif cpu_trend < -10:
                trends["cpu_trend"] = "decreasing"

            # Memory trend
            mem_values = [m.memory_usage for m in recent]
            mem_trend = mem_values[-1] - mem_values[0]
            if mem_trend > 10:
                trends["memory_trend"] = "increasing"
            elif mem_trend < -10:
                trends["memory_trend"] = "decreasing"

        return trends

    def _generate_recommendations(
        self,
        anomalies: List[Anomaly],
        ml_result: Optional[HybridAnomalyResult],
    ) -> List[str]:
        """Generate recommendations based on anomalies."""
        recommendations = []

        # ML-based recommendations
        if ml_result and ml_result.is_anomaly:
            if ml_result.source == AnomalySource.BOTH:
                recommendations.append(
                    "CRITICAL: Both temporal and pattern anomalies detected. "
                    "Immediate investigation recommended."
                )
            elif ml_result.source == AnomalySource.SARIMA:
                recommendations.append(
                    "Temporal anomaly detected. Current metrics deviate from expected patterns. "
                    "Monitor for persistent deviation."
                )
            elif ml_result.source == AnomalySource.ISOLATION:
                recommendations.append(
                    "Unusual metric combination detected. "
                    "Check correlation between highlighted metrics."
                )

            # Feature-specific recommendations
            if ml_result.feature_contributions:
                for feature, score in sorted(
                    ml_result.feature_contributions.items(),
                    key=lambda x: abs(x[1]),
                    reverse=True,
                )[:2]:
                    if abs(score) > 0.1:
                        msg = f"Review {feature}: Contributing to anomaly ({score:.2f})"
                        recommendations.append(msg)

        # Add anomaly-based recommendations
        recommendations.extend(generate_anomaly_recommendations(anomalies))

        return list(set(recommendations))  # Remove duplicates

    def get_statistics(self) -> Dict[str, Any]:
        """Get analyzer statistics."""
        return {
            "trained": self._trained,
            "history_length": len(self._metrics_history),
            "detector_stats": self._detector.get_statistics(),
        }

    def get_status(self) -> Dict[str, str]:
        """Get analyzer status."""
        return {
            "status": "active",
            "mode": "ml_hybrid" if self._trained else "static_fallback",
            "threshold": str(self.settings.anomaly_threshold),
        }

    async def health_check(self) -> Dict[str, Any]:
        """Check analyzer health."""
        detector_health = await self._detector.health_check()
        return {
            "healthy": detector_health["healthy"],
            "trained": self._trained,
            "detector": detector_health,
        }
