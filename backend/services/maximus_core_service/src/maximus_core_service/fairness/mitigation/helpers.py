"""Helper Functions for Mitigation Engine.

Common utilities used across mitigation strategies.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from ..base import FairnessException, MitigationResult

logger = logging.getLogger(__name__)


class HelpersMixin:
    """Mixin providing helper methods for mitigation strategies."""

    def _retrain_with_weights(
        self, model: Any, X: np.ndarray, y: np.ndarray, weights: np.ndarray
    ) -> Any:
        """Retrain model with sample weights.

        Args:
            model: Original model
            X: Training features
            y: Training labels
            weights: Sample weights

        Returns:
            Retrained model
        """
        if hasattr(model, "fit"):
            try:
                model.fit(X, y, sample_weight=weights)
            except TypeError:
                logger.warning(
                    "Model doesn't support sample_weight, fitting without weights"
                )
                model.fit(X, y)

        return model

    def _get_predictions(self, model: Any, X: np.ndarray) -> np.ndarray:
        """Get predictions from model.

        Args:
            model: Trained model
            X: Features

        Returns:
            Predictions array
        """
        if hasattr(model, "predict_proba"):
            return model.predict_proba(X)[:, 1]
        if hasattr(model, "predict"):
            return model.predict(X)
        raise FairnessException("Model has no predict or predict_proba method")

    def _evaluate_fairness(
        self,
        predictions: np.ndarray,
        true_labels: np.ndarray,
        protected_attribute: np.ndarray,
        protected_value: Any,
    ) -> dict[str, float]:
        """Evaluate fairness metrics.

        Args:
            predictions: Predictions
            true_labels: True labels
            protected_attribute: Protected attribute
            protected_value: Protected group value

        Returns:
            Dictionary of fairness metrics
        """
        results = self.fairness_constraints.evaluate_all_metrics(
            predictions, true_labels, protected_attribute, protected_value
        )

        fairness_dict = {}
        for metric, result in results.items():
            fairness_dict[f"{metric.value}_difference"] = result.difference
            fairness_dict[f"{metric.value}_ratio"] = result.ratio
            fairness_dict[f"{metric.value}_is_fair"] = 1.0 if result.is_fair else 0.0

        return fairness_dict

    def _evaluate_performance(
        self, predictions: np.ndarray, true_labels: np.ndarray
    ) -> dict[str, float]:
        """Evaluate model performance.

        Args:
            predictions: Predictions
            true_labels: True labels

        Returns:
            Dictionary of performance metrics
        """
        if predictions.dtype == float:
            binary_preds = (predictions > 0.5).astype(int)
        else:
            binary_preds = predictions

        accuracy = np.mean(binary_preds == true_labels)

        tp = np.sum((binary_preds == 1) & (true_labels == 1))
        fp = np.sum((binary_preds == 1) & (true_labels == 0))
        fn = np.sum((binary_preds == 0) & (true_labels == 1))

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        return {
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
        }

    def _check_fairness_improvement(
        self, before: dict[str, float], after: dict[str, float]
    ) -> bool:
        """Check if fairness improved.

        Args:
            before: Fairness metrics before mitigation
            after: Fairness metrics after mitigation

        Returns:
            True if fairness improved
        """
        if not before or not after:
            return False

        for key in before:
            if "_difference" in key and key in after:
                if before[key] - after[key] > self.fairness_improvement_threshold:
                    return True

        return False

    def _check_performance_acceptable(
        self, before: dict[str, float], after: dict[str, float]
    ) -> bool:
        """Check if performance is acceptable after mitigation.

        Args:
            before: Performance metrics before
            after: Performance metrics after

        Returns:
            True if performance is acceptable
        """
        if not before or not after:
            return True

        accuracy_before = before.get("accuracy", 0)
        accuracy_after = after.get("accuracy", 0)

        if accuracy_after < self.performance_threshold:
            return False

        if accuracy_before - accuracy_after > self.max_performance_loss:
            return False

        return True

    def _select_best_result(self, results: list[MitigationResult]) -> MitigationResult:
        """Select best mitigation result.

        Args:
            results: List of mitigation results

        Returns:
            Best result
        """
        if not results:
            raise FairnessException("No results to select from")

        successful = [r for r in results if r.success]

        if successful:
            best = max(
                successful,
                key=lambda r: sum(
                    r.fairness_before.get(k, 0) - r.fairness_after.get(k, 0)
                    for k in r.fairness_before.keys()
                    if "_difference" in k
                ),
            )
            return best

        best = min(results, key=lambda r: abs(r.performance_impact.get("accuracy", 0)))
        return best
