"""Bias Detector.

Main bias detection class for cybersecurity AI models.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from ..base import BiasDetectionResult
from .detectors import DetectorMixin
from .utils import UtilsMixin

logger = logging.getLogger(__name__)


class BiasDetector(DetectorMixin, UtilsMixin):
    """Bias detector for cybersecurity AI models.

    Implements multiple statistical tests and methods to detect bias
    in model predictions across different protected groups.

    Attributes:
        min_sample_size: Minimum samples required per group.
        significance_level: Statistical significance level (alpha).
        disparate_impact_threshold: Threshold for disparate impact.
        effect_size_thresholds: Thresholds for Cohen's d effect size.
        sensitivity: Detection sensitivity level.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize BiasDetector.

        Args:
            config: Configuration dictionary.
        """
        config = config or {}

        self.min_sample_size = config.get("min_sample_size", 30)
        self.significance_level = config.get("significance_level", 0.05)
        self.disparate_impact_threshold = config.get(
            "disparate_impact_threshold", 0.8
        )

        self.effect_size_thresholds = config.get(
            "effect_size_thresholds",
            {"small": 0.2, "medium": 0.5, "large": 0.8},
        )

        self.sensitivity = config.get("sensitivity", "medium")

        logger.info(
            "BiasDetector initialized with significance_level=%.2f, sensitivity=%s",
            self.significance_level,
            self.sensitivity,
        )

    def detect_all_biases(
        self,
        predictions: np.ndarray,
        protected_attribute: np.ndarray,
        true_labels: np.ndarray | None = None,
        protected_value: Any = 1,
    ) -> dict[str, BiasDetectionResult]:
        """Run all applicable bias detection methods.

        Args:
            predictions: Model predictions.
            protected_attribute: Protected attribute values.
            true_labels: True labels (optional).
            protected_value: Value indicating protected group.

        Returns:
            Dictionary mapping method names to results.
        """
        results: dict[str, BiasDetectionResult] = {}

        try:
            results["statistical_parity"] = self.detect_statistical_parity_bias(
                predictions, protected_attribute, protected_value
            )
        except Exception as e:
            logger.error("Statistical parity detection failed: %s", e)

        try:
            results["disparate_impact"] = self.detect_disparate_impact(
                predictions, protected_attribute, protected_value
            )
        except Exception as e:
            logger.error("Disparate impact detection failed: %s", e)

        try:
            results["distribution"] = self.detect_distribution_bias(
                predictions, protected_attribute, protected_value
            )
        except Exception as e:
            logger.error("Distribution bias detection failed: %s", e)

        if true_labels is not None:
            try:
                results["performance_disparity"] = self.detect_performance_disparity(
                    predictions, true_labels, protected_attribute, protected_value
                )
            except Exception as e:
                logger.error("Performance disparity detection failed: %s", e)

        return results
