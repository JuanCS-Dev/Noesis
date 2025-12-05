"""
Isolation Forest Anomaly Detector
=================================

Implements Isolation Forest for multivariate anomaly detection.
Complements SARIMA for detecting point anomalies in high-dimensional data.

Based on:
- Liu, Ting, Zhou (2008): Isolation Forest
- scikit-learn IsolationForest implementation
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class IsolationConfig:  # pylint: disable=too-many-instance-attributes
    """Configuration for Isolation Forest."""

    n_estimators: int = 100
    max_samples: str | int = "auto"
    contamination: float = 0.1  # Expected proportion of anomalies
    max_features: float = 1.0
    bootstrap: bool = False
    random_state: int = 42

    # Anomaly threshold (lower = more anomalous)
    anomaly_threshold: float = -0.5

    # Feature names for interpretability
    feature_names: List[str] = field(default_factory=list)


@dataclass
class AnomalyResult:
    """Result of anomaly detection."""

    is_anomaly: bool = False
    anomaly_score: float = 0.0
    feature_contributions: Dict[str, float] = field(default_factory=dict)
    raw_score: float = 0.0
    threshold: float = -0.5


class IsolationAnomalyDetector:
    """
    Isolation Forest based anomaly detector.

    Features:
    - Multivariate anomaly detection
    - Feature importance for interpretability
    - Online updates
    - Configurable contamination rate

    Example:
        >>> detector = IsolationAnomalyDetector()
        >>> detector.fit(training_data)  # [[cpu, memory, latency], ...]
        >>> result = detector.detect([95.0, 88.0, 500.0])
        >>> print(f"Anomaly: {result.is_anomaly}, Score: {result.anomaly_score}")
    """

    def __init__(self, config: Optional[IsolationConfig] = None):
        """Initialize Isolation Forest detector."""
        self.config = config or IsolationConfig()
        self._model: Any = None
        self._fitted = False
        self._training_data: List[List[float]] = []
        self._last_fit_time: Optional[datetime] = None
        self._feature_means: Optional[np.ndarray] = None
        self._feature_stds: Optional[np.ndarray] = None

        logger.info(
            "isolation_detector_initialized",
            extra={
                "n_estimators": self.config.n_estimators,
                "contamination": self.config.contamination,
            },
        )

    def fit(self, data: List[List[float]]) -> bool:
        """
        Fit Isolation Forest model.

        Args:
            data: Training data as list of feature vectors

        Returns:
            True if fitting succeeded
        """
        if len(data) < 10:
            logger.warning(
                "insufficient_training_data",
                extra={"data_length": len(data), "min_required": 10},
            )
            return False

        self._training_data = list(data)
        x_data = np.array(data)

        # Store statistics for normalization
        self._feature_means = np.mean(x_data, axis=0)
        feature_stds = np.std(x_data, axis=0)
        feature_stds[feature_stds == 0] = 1.0  # Avoid division by zero
        self._feature_stds = feature_stds

        try:
            # pylint: disable=import-outside-toplevel
            from sklearn.ensemble import IsolationForest

            self._model = IsolationForest(
                n_estimators=self.config.n_estimators,
                max_samples=self.config.max_samples,
                contamination=self.config.contamination,
                max_features=self.config.max_features,
                bootstrap=self.config.bootstrap,
                random_state=self.config.random_state,
                n_jobs=-1,
            )

            self._model.fit(x_data)
            self._fitted = True
            self._last_fit_time = datetime.utcnow()

            logger.info(
                "isolation_forest_fitted",
                extra={
                    "n_samples": len(data),
                    "n_features": x_data.shape[1] if len(x_data.shape) > 1 else 1,
                },
            )

            return True

        except ImportError:
            logger.warning("sklearn_not_available")
            return self._fit_simple_model(data)

        except (ValueError, RuntimeError) as exc:
            logger.error("isolation_fit_failed", extra={"error": str(exc)})
            return self._fit_simple_model(data)

    def _fit_simple_model(self, data: List[List[float]]) -> bool:
        """
        Fallback simple model when sklearn unavailable.

        Uses z-score based detection.
        """
        x_data = np.array(data)
        self._feature_means = np.mean(x_data, axis=0)
        feature_stds = np.std(x_data, axis=0)
        feature_stds[feature_stds == 0] = 1.0
        self._feature_stds = feature_stds

        self._fitted = True
        self._last_fit_time = datetime.utcnow()

        logger.info(
            "simple_zscore_model_fitted",
            extra={"n_samples": len(data)},
        )

        return True

    def detect(self, sample: List[float]) -> AnomalyResult:
        """
        Detect if a sample is anomalous.

        Args:
            sample: Feature vector to check

        Returns:
            AnomalyResult with detection details
        """
        result = AnomalyResult(threshold=self.config.anomaly_threshold)

        if not self._fitted:
            logger.warning("model_not_fitted")
            return result

        x_sample = np.array([sample])

        if self._model is not None:
            try:
                # Get anomaly score (-1 for anomalies, 1 for normal)
                prediction = self._model.predict(x_sample)[0]
                raw_score = self._model.score_samples(x_sample)[0]

                result.is_anomaly = prediction == -1
                result.raw_score = float(raw_score)
                result.anomaly_score = -raw_score  # Invert so higher = more anomalous

                # Calculate feature contributions
                result.feature_contributions = self._calculate_contributions(sample)

                return result

            except (ValueError, RuntimeError) as exc:
                logger.error("isolation_detect_failed", extra={"error": str(exc)})

        # Fallback to z-score detection
        return self._detect_simple(sample)

    def _detect_simple(self, sample: List[float]) -> AnomalyResult:
        """Simple z-score based detection fallback."""
        result = AnomalyResult(threshold=self.config.anomaly_threshold)

        if self._feature_means is None or self._feature_stds is None:
            return result

        x_arr = np.array(sample)
        z_scores = np.abs((x_arr - self._feature_means) / self._feature_stds)

        # Max z-score as anomaly indicator
        max_z = float(np.max(z_scores))
        mean_z = float(np.mean(z_scores))

        # Convert to anomaly score (higher = more anomalous)
        result.anomaly_score = mean_z
        result.raw_score = -mean_z  # Negative for consistency with IsolationForest
        result.is_anomaly = max_z > 3.0  # 3 sigma rule

        # Feature contributions
        feature_names = self.config.feature_names or [
            f"feature_{i}" for i in range(len(sample))
        ]
        result.feature_contributions = {
            name: float(z) for name, z in zip(feature_names, z_scores)
        }

        return result

    def _calculate_contributions(self, sample: List[float]) -> Dict[str, float]:
        """
        Calculate feature contributions to anomaly score.

        Uses perturbation-based approach for interpretability.
        """
        if self._feature_means is None or self._model is None:
            return {}

        contributions = {}
        feature_names = self.config.feature_names or [
            f"feature_{i}" for i in range(len(sample))
        ]

        # Baseline score
        baseline = self._model.score_samples(np.array([sample]))[0]

        # Perturb each feature to mean and measure impact
        for i, name in enumerate(feature_names):
            perturbed = list(sample)
            perturbed[i] = float(self._feature_means[i])

            perturbed_score = self._model.score_samples(np.array([perturbed]))[0]

            # Positive contribution = feature increases anomaly score
            contributions[name] = float(baseline - perturbed_score)

        return contributions

    def detect_batch(self, samples: List[List[float]]) -> List[AnomalyResult]:
        """
        Detect anomalies in batch.

        Args:
            samples: List of feature vectors

        Returns:
            List of AnomalyResults
        """
        return [self.detect(sample) for sample in samples]

    def update(self, sample: List[float]) -> None:
        """
        Update model with new sample (online learning).

        Args:
            sample: New observed sample
        """
        self._training_data.append(sample)

        # Refit periodically
        if len(self._training_data) % 500 == 0:
            logger.info(
                "refitting_isolation_forest",
                extra={"training_size": len(self._training_data)},
            )
            self.fit(self._training_data)

    def get_diagnostics(self) -> Dict[str, Any]:
        """Get model diagnostics."""
        return {
            "model_type": "IsolationForest",
            "fitted": self._fitted,
            "training_samples": len(self._training_data),
            "last_fit_time": (
                self._last_fit_time.isoformat() if self._last_fit_time else None
            ),
            "config": {
                "n_estimators": self.config.n_estimators,
                "contamination": self.config.contamination,
                "anomaly_threshold": self.config.anomaly_threshold,
            },
            "feature_names": self.config.feature_names,
        }

    async def health_check(self) -> Dict[str, Any]:
        """Check health of detector."""
        return {
            "healthy": True,
            "model_fitted": self._fitted,
            "training_samples": len(self._training_data),
        }
