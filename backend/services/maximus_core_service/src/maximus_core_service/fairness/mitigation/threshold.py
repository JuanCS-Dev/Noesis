"""Threshold Optimization Mitigation Strategy.

Post-processing mitigation by optimizing classification thresholds.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from ..base import FairnessMetric, MitigationResult, ProtectedAttribute

logger = logging.getLogger(__name__)


class ThresholdMixin:
    """Mixin providing threshold optimization mitigation strategy."""

    def mitigate_threshold_optimization(
        self,
        predictions: np.ndarray,
        true_labels: np.ndarray,
        protected_attribute: np.ndarray,
        protected_value: Any = 1,
        metric: FairnessMetric = FairnessMetric.EQUALIZED_ODDS,
    ) -> MitigationResult:
        """Mitigate bias using threshold optimization (post-processing).

        Finds optimal classification thresholds for each group to satisfy
        fairness constraints while maintaining performance.

        Args:
            predictions: Model prediction scores (probabilities)
            true_labels: True labels
            protected_attribute: Protected attribute values
            protected_value: Value indicating protected group
            metric: Target fairness metric

        Returns:
            MitigationResult with mitigation outcome
        """
        logger.info(f"Starting threshold optimization for {metric.value}...")

        binary_preds_before = (predictions > 0.5).astype(int)
        fairness_before = self._evaluate_fairness(
            binary_preds_before, true_labels, protected_attribute, protected_value
        )
        performance_before = self._evaluate_performance(binary_preds_before, true_labels)

        threshold_0, threshold_1 = self._find_optimal_thresholds(
            predictions, true_labels, protected_attribute, protected_value, metric
        )

        group_0_mask = protected_attribute != protected_value
        group_1_mask = protected_attribute == protected_value

        binary_preds_after = np.zeros_like(predictions, dtype=int)
        binary_preds_after[group_0_mask] = (
            predictions[group_0_mask] > threshold_0
        ).astype(int)
        binary_preds_after[group_1_mask] = (
            predictions[group_1_mask] > threshold_1
        ).astype(int)

        fairness_after = self._evaluate_fairness(
            binary_preds_after, true_labels, protected_attribute, protected_value
        )
        performance_after = self._evaluate_performance(binary_preds_after, true_labels)

        performance_impact = {
            key: performance_after.get(key, 0) - performance_before.get(key, 0)
            for key in performance_before.keys()
        }

        fairness_improved = self._check_fairness_improvement(fairness_before, fairness_after)
        performance_acceptable = self._check_performance_acceptable(
            performance_before, performance_after
        )

        success = fairness_improved and performance_acceptable

        result = MitigationResult(
            mitigation_method="threshold_optimization",
            protected_attribute=ProtectedAttribute.GEOGRAPHIC_LOCATION,
            fairness_before=fairness_before,
            fairness_after=fairness_after,
            performance_impact=performance_impact,
            success=success,
            metadata={
                "threshold_group_0": float(threshold_0),
                "threshold_group_1": float(threshold_1),
                "target_metric": metric.value,
                "performance_before": performance_before,
                "performance_after": performance_after,
            },
        )

        logger.info(
            f"Threshold optimization complete: success={success}, "
            f"thresholds=({threshold_0:.3f}, {threshold_1:.3f})"
        )

        return result

    def _find_optimal_thresholds(
        self,
        predictions: np.ndarray,
        true_labels: np.ndarray,
        protected_attribute: np.ndarray,
        protected_value: Any,
        metric: FairnessMetric,
    ) -> tuple[float, float]:
        """Find optimal classification thresholds for each group.

        Args:
            predictions: Prediction scores
            true_labels: True labels
            protected_attribute: Protected attribute values
            protected_value: Value indicating protected group
            metric: Target fairness metric

        Returns:
            Tuple of (threshold_group_0, threshold_group_1)
        """
        thresholds = np.linspace(0.1, 0.9, 50)

        best_score = float("-inf")
        best_thresholds = (0.5, 0.5)

        group_0_mask = protected_attribute != protected_value
        group_1_mask = protected_attribute == protected_value

        for t0 in thresholds:
            for t1 in thresholds:
                binary_preds = np.zeros_like(predictions, dtype=int)
                binary_preds[group_0_mask] = (predictions[group_0_mask] > t0).astype(int)
                binary_preds[group_1_mask] = (predictions[group_1_mask] > t1).astype(int)

                fairness_results = self.fairness_constraints.evaluate_all_metrics(
                    binary_preds, true_labels, protected_attribute, protected_value
                )

                accuracy = np.mean(binary_preds == true_labels)

                fairness_score = 0.0
                if metric in fairness_results:
                    fairness_score = 1.0 - fairness_results[metric].difference

                combined_score = 0.6 * fairness_score + 0.4 * accuracy

                if combined_score > best_score:
                    best_score = combined_score
                    best_thresholds = (t0, t1)

        return best_thresholds
