"""Calibration Adjustment Mitigation Strategy.

Post-processing mitigation by adjusting prediction calibration.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression

from ..base import MitigationResult, ProtectedAttribute

logger = logging.getLogger(__name__)


class CalibrationMixin:
    """Mixin providing calibration adjustment mitigation strategy."""

    def mitigate_calibration_adjustment(
        self,
        predictions: np.ndarray,
        true_labels: np.ndarray,
        protected_attribute: np.ndarray,
        protected_value: Any = 1,
    ) -> MitigationResult:
        """Mitigate bias using calibration adjustment (post-processing).

        Adjusts prediction scores to ensure equal calibration across groups.

        Args:
            predictions: Model prediction scores
            true_labels: True labels
            protected_attribute: Protected attribute values
            protected_value: Value indicating protected group

        Returns:
            MitigationResult with mitigation outcome
        """
        logger.info("Starting calibration adjustment mitigation...")

        binary_preds_before = (predictions > 0.5).astype(int)
        fairness_before = self._evaluate_fairness(
            binary_preds_before, true_labels, protected_attribute, protected_value
        )
        performance_before = self._evaluate_performance(binary_preds_before, true_labels)

        group_0_mask = protected_attribute != protected_value
        group_1_mask = protected_attribute == protected_value

        calibrator_0 = self._fit_calibrator(
            predictions[group_0_mask], true_labels[group_0_mask]
        )
        calibrator_1 = self._fit_calibrator(
            predictions[group_1_mask], true_labels[group_1_mask]
        )

        adjusted_predictions = predictions.copy()
        adjusted_predictions[group_0_mask] = calibrator_0(predictions[group_0_mask])
        adjusted_predictions[group_1_mask] = calibrator_1(predictions[group_1_mask])

        adjusted_predictions = np.clip(adjusted_predictions, 0, 1)

        binary_preds_after = (adjusted_predictions > 0.5).astype(int)
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
            mitigation_method="calibration_adjustment",
            protected_attribute=ProtectedAttribute.GEOGRAPHIC_LOCATION,
            fairness_before=fairness_before,
            fairness_after=fairness_after,
            performance_impact=performance_impact,
            success=success,
            metadata={
                "predictions_before_mean": float(np.mean(predictions)),
                "predictions_after_mean": float(np.mean(adjusted_predictions)),
                "performance_before": performance_before,
                "performance_after": performance_after,
            },
        )

        logger.info(f"Calibration adjustment complete: success={success}")

        return result

    def _fit_calibrator(
        self, predictions: np.ndarray, true_labels: np.ndarray
    ) -> Callable:
        """Fit isotonic calibration model.

        Args:
            predictions: Prediction scores
            true_labels: True labels

        Returns:
            Calibration function
        """
        X = predictions.reshape(-1, 1)
        y = true_labels

        calibrator = LogisticRegression(max_iter=1000)
        calibrator.fit(X, y)

        def calibrate(scores: np.ndarray) -> np.ndarray:
            return calibrator.predict_proba(scores.reshape(-1, 1))[:, 1]

        return calibrate
