"""Interpretable Model for LIME.

Linear model fitting and prediction.
"""

from __future__ import annotations

from typing import Any

import numpy as np


class InterpretableMixin:
    """Mixin providing interpretable model methods."""

    def _get_model_predictions(
        self, model: Any, samples: list[dict[str, Any]]
    ) -> np.ndarray:
        """Get model predictions for perturbed samples.

        Args:
            model: The model
            samples: List of perturbed samples

        Returns:
            Array of predictions
        """
        if hasattr(model, "predict_proba"):
            X = self._samples_to_model_input(samples, model)
            proba = model.predict_proba(X)

            if proba.ndim == 2:
                return proba[:, -1]
            return proba

        if hasattr(model, "predict"):
            X = self._samples_to_model_input(samples, model)
            return model.predict(X)

        raise ValueError("Model must have 'predict' or 'predict_proba' method")

    def _samples_to_model_input(
        self, samples: list[dict[str, Any]], model: Any
    ) -> Any:
        """Convert samples to model input format.

        Args:
            samples: List of sample dicts
            model: The model

        Returns:
            Input in format expected by model
        """
        meta_fields = {"decision_id", "timestamp", "analysis_id"}
        feature_names = sorted([k for k in samples[0].keys() if k not in meta_fields])

        X = np.array(
            [[sample.get(f, 0) for f in feature_names] for sample in samples]
        )

        return X

    def _calculate_kernel_weights(
        self, distances: np.ndarray, kernel_width: float
    ) -> np.ndarray:
        """Calculate kernel weights for samples.

        Args:
            distances: Array of distances from original instance
            kernel_width: Width of exponential kernel

        Returns:
            Array of weights
        """
        return np.exp(-(distances**2) / (kernel_width**2))

    def _fit_interpretable_model(
        self,
        samples: list[dict[str, Any]],
        predictions: np.ndarray,
        weights: np.ndarray,
        feature_names: list[str],
    ) -> dict[str, float]:
        """Fit weighted linear regression model.

        Args:
            samples: Perturbed samples
            predictions: Model predictions
            weights: Sample weights
            feature_names: Feature names

        Returns:
            Dictionary of feature importances (coefficients)
        """
        from sklearn.linear_model import Ridge

        meta_fields = {"decision_id", "timestamp", "analysis_id"}
        feature_names = sorted([f for f in feature_names if f not in meta_fields])

        X = np.array(
            [[sample.get(f, 0) for f in feature_names] for sample in samples]
        )

        model = Ridge(alpha=1.0)
        model.fit(X, predictions, sample_weight=weights)

        importances = {}
        for i, feature_name in enumerate(feature_names):
            importances[feature_name] = float(model.coef_[i])

        importances["__intercept__"] = float(model.intercept_)

        return importances

    def _predict_interpretable_model(
        self, samples: list[dict[str, Any]], importances: dict[str, float]
    ) -> np.ndarray:
        """Predict using interpretable model.

        Args:
            samples: Samples to predict
            importances: Feature importances (coefficients)

        Returns:
            Predictions
        """
        meta_fields = {"decision_id", "timestamp", "analysis_id", "__intercept__"}
        feature_names = sorted([f for f in importances if f not in meta_fields])

        X = np.array(
            [[sample.get(f, 0) for f in feature_names] for sample in samples]
        )
        coefficients = np.array([importances[f] for f in feature_names])

        intercept = importances.get("__intercept__", 0.0)
        return X.dot(coefficients) + intercept

    def _calculate_explanation_confidence(
        self,
        true_predictions: np.ndarray,
        interpretable_predictions: np.ndarray,
        weights: np.ndarray,
    ) -> float:
        """Calculate explanation confidence (weighted R²).

        Args:
            true_predictions: Model's predictions
            interpretable_predictions: Interpretable model's predictions
            weights: Sample weights

        Returns:
            R² score (confidence)
        """
        residuals = true_predictions - interpretable_predictions
        ss_res = np.sum(weights * (residuals**2))

        mean_pred = np.average(true_predictions, weights=weights)
        ss_tot = np.sum(weights * ((true_predictions - mean_pred) ** 2))

        if ss_tot == 0:
            if ss_res == 0:
                return 1.0
            return 0.0

        r_squared = 1 - (ss_res / ss_tot)
        return max(0.0, min(1.0, r_squared))
