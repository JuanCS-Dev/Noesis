"""Bias Detection Utilities.

Utility methods for bias detection.
"""

from __future__ import annotations

import numpy as np


class UtilsMixin:
    """Mixin providing utility methods.

    Provides helper methods for:
    - Severity determination
    - Effect size categorization
    - F1 score calculation
    """

    effect_size_thresholds: dict[str, float]
    significance_level: float

    def _determine_severity(
        self, p_value: float, effect_size: float, method: str
    ) -> str:
        """Determine severity of bias based on p-value and effect size.

        Args:
            p_value: Statistical p-value.
            effect_size: Effect size measure.
            method: Detection method used.

        Returns:
            Severity level: low, medium, high, or critical.
        """
        if p_value < 0.001 and effect_size > self.effect_size_thresholds["large"]:
            return "critical"

        if p_value < 0.01 and effect_size > self.effect_size_thresholds["medium"]:
            return "high"

        if (
            p_value < self.significance_level
            and effect_size > self.effect_size_thresholds["small"]
        ):
            return "medium"

        return "low"

    def _categorize_effect_size(self, cohens_d: float) -> str:
        """Categorize Cohen's d effect size.

        Args:
            cohens_d: Cohen's d value.

        Returns:
            Category: negligible, small, medium, large, or very_large.
        """
        abs_d = abs(cohens_d)

        if abs_d < self.effect_size_thresholds["small"]:
            return "negligible"
        if abs_d < self.effect_size_thresholds["medium"]:
            return "small"
        if abs_d < self.effect_size_thresholds["large"]:
            return "medium"
        if abs_d < 1.2:
            return "large"
        return "very_large"

    def _calculate_f1_score(
        self, predictions: np.ndarray, true_labels: np.ndarray
    ) -> float:
        """Calculate F1 score.

        Args:
            predictions: Binary predictions.
            true_labels: True labels.

        Returns:
            F1 score.
        """
        tp = np.sum((predictions == 1) & (true_labels == 1))
        fp = np.sum((predictions == 1) & (true_labels == 0))
        fn = np.sum((predictions == 0) & (true_labels == 1))

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        f1 = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        return f1
