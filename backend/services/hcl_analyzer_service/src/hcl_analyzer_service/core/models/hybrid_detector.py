"""
Hybrid Anomaly Detector - SARIMA + Isolation Forest
===================================================

Combines time series forecasting (SARIMA) with multivariate
anomaly detection (Isolation Forest) for robust detection.

Architecture:
1. SARIMA: Detects temporal anomalies (deviations from forecast)
2. IsolationForest: Detects point anomalies (unusual feature combinations)
3. Ensemble: Combines both signals with configurable weights

Based on:
- SARIMA-LSTM Hybrid research (2025)
- Multi-model ensemble anomaly detection
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import numpy as np

from .sarima_forecaster import SARIMAForecaster, SARIMAConfig
from .isolation_detector import IsolationAnomalyDetector, IsolationConfig

logger = logging.getLogger(__name__)


class AnomalySource(str, Enum):
    """Source of anomaly detection."""

    SARIMA = "sarima"
    ISOLATION = "isolation"
    BOTH = "both"
    NONE = "none"


@dataclass
class HybridConfig:  # pylint: disable=too-many-instance-attributes
    """Configuration for hybrid detector."""

    # Component weights (must sum to 1.0)
    sarima_weight: float = 0.4
    isolation_weight: float = 0.6

    # Thresholds
    sarima_sigma_threshold: float = 2.5
    isolation_score_threshold: float = -0.3

    # Ensemble threshold for final decision
    ensemble_threshold: float = 0.5

    # Component configs
    sarima_config: Optional[SARIMAConfig] = None
    isolation_config: Optional[IsolationConfig] = None

    # Feature mapping for SARIMA (which metric to forecast)
    sarima_feature_index: int = 0  # Default to first feature (e.g., CPU)

    # Feature names
    feature_names: List[str] = field(
        default_factory=lambda: ["cpu_usage", "memory_usage", "error_rate", "latency_ms"]
    )


@dataclass
class HybridAnomalyResult:  # pylint: disable=too-many-instance-attributes
    """Result from hybrid anomaly detection."""

    is_anomaly: bool = False
    anomaly_score: float = 0.0
    source: AnomalySource = AnomalySource.NONE

    # Component results
    sarima_anomaly: bool = False
    sarima_score: float = 0.0
    sarima_expected: Optional[float] = None

    isolation_anomaly: bool = False
    isolation_score: float = 0.0
    feature_contributions: Dict[str, float] = field(default_factory=dict)

    # Ensemble details
    weighted_score: float = 0.0
    confidence: float = 0.0

    # Metadata
    timestamp: Optional[datetime] = None
    explanation: str = ""


class HybridAnomalyDetector:
    """
    Hybrid anomaly detector combining SARIMA and Isolation Forest.

    This detector provides robust anomaly detection by:
    1. Using SARIMA to detect temporal deviations (metric is higher/lower than expected)
    2. Using Isolation Forest to detect unusual feature combinations
    3. Combining both signals with configurable weights

    Example:
        >>> config = HybridConfig(
        ...     sarima_weight=0.4,
        ...     isolation_weight=0.6,
        ...     feature_names=["cpu", "memory", "latency"]
        ... )
        >>> detector = HybridAnomalyDetector(config)
        >>> detector.fit(
        ...     time_series=[50, 55, 52, 60, 58, ...],  # CPU history
        ...     multivariate_data=[[50, 60, 100], [55, 62, 110], ...]
        ... )
        >>> result = detector.detect(
        ...     time_series_value=95.0,  # Current CPU
        ...     feature_vector=[95.0, 88.0, 500.0]  # All metrics
        ... )
    """

    def __init__(self, config: Optional[HybridConfig] = None):
        """Initialize hybrid detector."""
        self.config = config or HybridConfig()

        # Initialize component detectors
        self._sarima = SARIMAForecaster(self.config.sarima_config)
        self._isolation = IsolationAnomalyDetector(self.config.isolation_config)

        # Update isolation feature names
        if self.config.feature_names:
            self._isolation.config.feature_names = self.config.feature_names

        self._fitted = False
        self._detection_history: List[HybridAnomalyResult] = []

        logger.info(
            "hybrid_detector_initialized",
            extra={
                "sarima_weight": self.config.sarima_weight,
                "isolation_weight": self.config.isolation_weight,
            },
        )

    def fit(
        self,
        time_series: List[float],
        multivariate_data: List[List[float]],
    ) -> bool:
        """
        Fit both component models.

        Args:
            time_series: Historical values for SARIMA (single metric)
            multivariate_data: Historical feature vectors for Isolation Forest

        Returns:
            True if both models fitted successfully
        """
        sarima_fitted = self._sarima.fit(time_series)
        isolation_fitted = self._isolation.fit(multivariate_data)

        self._fitted = sarima_fitted or isolation_fitted

        logger.info(
            "hybrid_detector_fitted",
            extra={
                "sarima_fitted": sarima_fitted,
                "isolation_fitted": isolation_fitted,
                "overall_fitted": self._fitted,
            },
        )

        return self._fitted

    def detect(
        self,
        time_series_value: float,
        feature_vector: List[float],
    ) -> HybridAnomalyResult:
        """
        Detect anomaly using both models.

        Args:
            time_series_value: Current value for SARIMA detection
            feature_vector: Current feature vector for Isolation Forest

        Returns:
            HybridAnomalyResult with combined detection
        """
        result = HybridAnomalyResult(timestamp=datetime.utcnow())

        # SARIMA detection
        sarima_is_anomaly, sarima_deviation = self._sarima.is_anomalous(
            time_series_value,
            threshold_sigma=self.config.sarima_sigma_threshold,
        )
        result.sarima_anomaly = sarima_is_anomaly
        result.sarima_score = sarima_deviation

        # Get SARIMA forecast for explanation
        forecast = self._sarima.predict(steps=1)
        if forecast.predicted_values:
            result.sarima_expected = forecast.predicted_values[0]

        # Isolation Forest detection
        iso_result = self._isolation.detect(feature_vector)
        result.isolation_anomaly = iso_result.is_anomaly
        result.isolation_score = iso_result.anomaly_score
        result.feature_contributions = iso_result.feature_contributions

        # Normalize scores for combination
        sarima_normalized = min(1.0, sarima_deviation / 5.0)  # Cap at 5 sigma
        isolation_normalized = min(
            1.0, max(0.0, -iso_result.raw_score)
        )  # Normalize IsolationForest score

        # Weighted combination
        result.weighted_score = (
            self.config.sarima_weight * sarima_normalized
            + self.config.isolation_weight * isolation_normalized
        )

        # Final decision
        result.is_anomaly = result.weighted_score > self.config.ensemble_threshold

        # Determine source
        if sarima_is_anomaly and iso_result.is_anomaly:
            result.source = AnomalySource.BOTH
        elif sarima_is_anomaly:
            result.source = AnomalySource.SARIMA
        elif iso_result.is_anomaly:
            result.source = AnomalySource.ISOLATION
        else:
            result.source = AnomalySource.NONE

        # Calculate confidence
        result.confidence = self._calculate_confidence(result)

        # Generate explanation
        result.explanation = self._generate_explanation(result, feature_vector)

        # Store result
        result.anomaly_score = result.weighted_score
        self._detection_history.append(result)

        # Trim history
        if len(self._detection_history) > 1000:
            self._detection_history = self._detection_history[-1000:]

        if result.is_anomaly:
            logger.info(
                "hybrid_anomaly_detected",
                extra={
                    "source": result.source.value,
                    "weighted_score": result.weighted_score,
                    "sarima_score": result.sarima_score,
                    "isolation_score": result.isolation_score,
                },
            )

        return result

    def _calculate_confidence(self, result: HybridAnomalyResult) -> float:
        """Calculate confidence in the detection."""
        # Higher confidence when both models agree
        if result.source == AnomalySource.BOTH:
            return 0.95
        if result.source == AnomalySource.NONE:
            return 0.9
        # Single model detection - moderate confidence
        return 0.7 + (result.weighted_score * 0.2)

    def _generate_explanation(
        self,
        result: HybridAnomalyResult,
        feature_vector: List[float],
    ) -> str:
        """Generate human-readable explanation."""
        if result.source == AnomalySource.NONE:
            return "No anomaly detected. All metrics within expected ranges."

        explanations = []

        if result.sarima_anomaly:
            expected = result.sarima_expected or 0
            feature_name = self.config.feature_names[self.config.sarima_feature_index]
            actual = feature_vector[self.config.sarima_feature_index]
            explanations.append(
                f"Temporal anomaly: {feature_name} is {actual:.1f} "
                f"(expected ~{expected:.1f}, deviation: {result.sarima_score:.2f}σ)"
            )

        if result.isolation_anomaly and result.feature_contributions:
            # Find top contributing features
            sorted_contrib = sorted(
                result.feature_contributions.items(),
                key=lambda x: abs(x[1]),
                reverse=True,
            )[:3]

            contrib_str = ", ".join(
                [f"{name}: {score:.2f}" for name, score in sorted_contrib]
            )
            explanations.append(f"Unusual feature combination detected. Top factors: {contrib_str}")

        if result.source == AnomalySource.BOTH:
            prefix = "CRITICAL: Both temporal and multivariate anomaly detected. "
        else:
            prefix = ""

        return prefix + " | ".join(explanations)

    def update(
        self,
        time_series_value: float,
        feature_vector: List[float],
    ) -> None:
        """
        Update models with new observation.

        Args:
            time_series_value: New time series value
            feature_vector: New feature vector
        """
        self._sarima.update(time_series_value)
        self._isolation.update(feature_vector)

    def detect_and_update(
        self,
        time_series_value: float,
        feature_vector: List[float],
    ) -> HybridAnomalyResult:
        """
        Detect anomaly and update models in one call.

        Args:
            time_series_value: Current value
            feature_vector: Current features

        Returns:
            Detection result
        """
        result = self.detect(time_series_value, feature_vector)
        self.update(time_series_value, feature_vector)
        return result

    def get_statistics(self) -> Dict[str, Any]:
        """Get detection statistics."""
        if not self._detection_history:
            return {"total_detections": 0}

        total = len(self._detection_history)
        anomalies = sum(1 for r in self._detection_history if r.is_anomaly)

        source_counts = {
            "sarima_only": sum(
                1 for r in self._detection_history if r.source == AnomalySource.SARIMA
            ),
            "isolation_only": sum(
                1 for r in self._detection_history if r.source == AnomalySource.ISOLATION
            ),
            "both": sum(
                1 for r in self._detection_history if r.source == AnomalySource.BOTH
            ),
        }

        return {
            "total_detections": total,
            "total_anomalies": anomalies,
            "anomaly_rate": anomalies / total if total > 0 else 0,
            "source_distribution": source_counts,
            "avg_weighted_score": np.mean(
                [r.weighted_score for r in self._detection_history]
            ),
        }

    def get_diagnostics(self) -> Dict[str, Any]:
        """Get comprehensive diagnostics."""
        return {
            "model_type": "HybridDetector",
            "fitted": self._fitted,
            "config": {
                "sarima_weight": self.config.sarima_weight,
                "isolation_weight": self.config.isolation_weight,
                "ensemble_threshold": self.config.ensemble_threshold,
            },
            "sarima_diagnostics": self._sarima.get_diagnostics(),
            "isolation_diagnostics": self._isolation.get_diagnostics(),
            "detection_statistics": self.get_statistics(),
        }

    async def health_check(self) -> Dict[str, Any]:
        """Check health of hybrid detector."""
        sarima_health = await self._sarima.health_check()
        isolation_health = await self._isolation.health_check()

        return {
            "healthy": sarima_health["healthy"] and isolation_health["healthy"],
            "fitted": self._fitted,
            "components": {
                "sarima": sarima_health,
                "isolation": isolation_health,
            },
            "detection_count": len(self._detection_history),
        }
