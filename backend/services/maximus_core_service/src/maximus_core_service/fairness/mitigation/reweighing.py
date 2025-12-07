"""Reweighing Mitigation Strategy.

Pre-processing mitigation by reweighing training samples.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from ..base import MitigationResult, ProtectedAttribute

logger = logging.getLogger(__name__)


class ReweighingMixin:
    """Mixin providing reweighing mitigation strategy."""

    def mitigate_reweighing(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        protected_attribute: np.ndarray,
        protected_value: Any = 1,
        model: Any | None = None,
    ) -> MitigationResult:
        """Mitigate bias using reweighing strategy (pre-processing).

        Assigns weights to training samples to balance representation across
        protected groups and outcome classes.

        Args:
            X_train: Training features
            y_train: Training labels
            protected_attribute: Protected attribute values
            protected_value: Value indicating protected group
            model: Model to retrain (optional)

        Returns:
            MitigationResult with mitigation outcome
        """
        logger.info("Starting reweighing mitigation...")

        weights = self._calculate_reweighing_weights(
            y_train, protected_attribute, protected_value
        )

        if model is not None:
            predictions_before = self._get_predictions(model, X_train)
            fairness_before = self._evaluate_fairness(
                predictions_before, y_train, protected_attribute, protected_value
            )
            performance_before = self._evaluate_performance(predictions_before, y_train)
        else:
            fairness_before = {}
            performance_before = {}

        if model is not None:
            model_after = self._retrain_with_weights(model, X_train, y_train, weights)
            predictions_after = self._get_predictions(model_after, X_train)
            fairness_after = self._evaluate_fairness(
                predictions_after, y_train, protected_attribute, protected_value
            )
            performance_after = self._evaluate_performance(predictions_after, y_train)
        else:
            fairness_after = fairness_before
            performance_after = performance_before

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
            mitigation_method="reweighing",
            protected_attribute=ProtectedAttribute.GEOGRAPHIC_LOCATION,
            fairness_before=fairness_before,
            fairness_after=fairness_after,
            performance_impact=performance_impact,
            success=success,
            metadata={
                "weights_min": float(np.min(weights)),
                "weights_max": float(np.max(weights)),
                "weights_mean": float(np.mean(weights)),
                "weights_std": float(np.std(weights)),
                "performance_before": performance_before,
                "performance_after": performance_after,
            },
        )

        logger.info(
            f"Reweighing complete: success={success}, "
            f"fairness_improved={fairness_improved}, "
            f"performance_acceptable={performance_acceptable}"
        )

        return result

    def _calculate_reweighing_weights(
        self, y: np.ndarray, protected_attribute: np.ndarray, protected_value: Any
    ) -> np.ndarray:
        """Calculate reweighing weights for training samples.

        Args:
            y: Labels
            protected_attribute: Protected attribute values
            protected_value: Value indicating protected group

        Returns:
            Sample weights array
        """
        weights = np.ones(len(y))

        n = len(y)
        n_pos = np.sum(y == 1)
        n_neg = np.sum(y == 0)

        group_0_mask = protected_attribute != protected_value
        group_1_mask = protected_attribute == protected_value

        n_0 = np.sum(group_0_mask)
        n_1 = np.sum(group_1_mask)

        p_y_pos = n_pos / n
        p_y_neg = n_neg / n
        p_a_0 = n_0 / n
        p_a_1 = n_1 / n

        n_0_pos = np.sum((group_0_mask) & (y == 1))
        n_0_neg = np.sum((group_0_mask) & (y == 0))
        n_1_pos = np.sum((group_1_mask) & (y == 1))
        n_1_neg = np.sum((group_1_mask) & (y == 0))

        p_0_pos = n_0_pos / n if n_0_pos > 0 else 0.0001
        p_0_neg = n_0_neg / n if n_0_neg > 0 else 0.0001
        p_1_pos = n_1_pos / n if n_1_pos > 0 else 0.0001
        p_1_neg = n_1_neg / n if n_1_neg > 0 else 0.0001

        w_0_pos = (p_y_pos * p_a_0) / p_0_pos if p_0_pos > 0 else 1.0
        w_0_neg = (p_y_neg * p_a_0) / p_0_neg if p_0_neg > 0 else 1.0
        w_1_pos = (p_y_pos * p_a_1) / p_1_pos if p_1_pos > 0 else 1.0
        w_1_neg = (p_y_neg * p_a_1) / p_1_neg if p_1_neg > 0 else 1.0

        weights[(group_0_mask) & (y == 1)] = w_0_pos
        weights[(group_0_mask) & (y == 0)] = w_0_neg
        weights[(group_1_mask) & (y == 1)] = w_1_pos
        weights[(group_1_mask) & (y == 0)] = w_1_neg

        return weights
