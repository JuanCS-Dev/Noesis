"""SHAP Algorithm Implementations.

Provides different SHAP algorithm implementations:
- Kernel SHAP (model-agnostic)
- Tree SHAP
- Linear SHAP
- Deep SHAP
"""

from __future__ import annotations

import logging
from typing import Any, Protocol

import numpy as np

logger = logging.getLogger(__name__)


class ModelProtocol(Protocol):
    """Protocol for models that can be explained."""

    def predict(self, x: np.ndarray) -> np.ndarray:
        """Make predictions."""


def get_prediction(model: Any, instance: np.ndarray) -> float:
    """Get model prediction for instance.

    Args:
        model: The model.
        instance: Instance as numpy array.

    Returns:
        Prediction value (float).

    Raises:
        ValueError: If model has no predict method.
    """
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(instance)
        if proba.ndim == 2:
            return float(proba[0, -1])
        return float(proba[0])

    if hasattr(model, "predict"):
        pred = model.predict(instance)
        return float(pred[0])

    raise ValueError("Model must have 'predict' or 'predict_proba' method")


def compute_kernel_shap(
    model: Any,
    instance: np.ndarray,
    background_data: np.ndarray | None,
    check_additivity: bool = False,
) -> np.ndarray:
    """Compute SHAP values using Kernel SHAP (model-agnostic).

    This is a simplified implementation based on weighted linear regression
    of coalition outcomes.

    Args:
        model: The model.
        instance: Instance as numpy array (1 x M).
        background_data: Background samples for comparison.
        check_additivity: Whether to check SHAP value additivity.

    Returns:
        Array of SHAP values.
    """
    num_features = instance.shape[1]

    full_pred = get_prediction(model, instance)

    if background_data is None:
        background = np.zeros_like(instance)
        background_pred = get_prediction(model, background)
    else:
        background = background_data[:1]
        background_pred = get_prediction(model, background)

    shap_values = np.zeros(num_features)

    for i in range(num_features):
        instance_without_i = instance.copy()
        instance_without_i[0, i] = background[0, i]

        pred_without_i = get_prediction(model, instance_without_i)
        shap_values[i] = full_pred - pred_without_i

    if check_additivity:
        total = np.sum(shap_values)
        expected_total = full_pred - background_pred

        if abs(total - expected_total) > 0.01:
            logger.warning(
                f"SHAP values do not add up: "
                f"sum={total:.4f}, expected={expected_total:.4f}"
            )

    return shap_values


def compute_tree_shap(model: Any, instance: np.ndarray) -> np.ndarray:
    """Compute SHAP values for tree-based models.

    This uses a simplified method based on feature importances.
    For production, consider using the official shap library's TreeExplainer.

    Args:
        model: Tree-based model.
        instance: Instance as numpy array.

    Returns:
        Array of SHAP values.
    """
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    else:
        logger.warning(
            "Model has no feature_importances_, falling back to kernel SHAP"
        )
        return compute_kernel_shap(model, instance, None)

    shap_values = importances * instance[0]
    return shap_values


def compute_linear_shap(
    model: Any, instance: np.ndarray, background_data: np.ndarray | None
) -> np.ndarray:
    """Compute SHAP values for linear models.

    For linear models, SHAP values = coefficients * (feature - mean).

    Args:
        model: Linear model.
        instance: Instance as numpy array.
        background_data: Background data for mean calculation.

    Returns:
        Array of SHAP values.
    """
    if hasattr(model, "coef_"):
        coefficients = model.coef_

        if coefficients.ndim > 1:
            coefficients = coefficients[-1]
    else:
        logger.warning("Model has no coef_, falling back to kernel SHAP")
        return compute_kernel_shap(model, instance, background_data)

    if background_data is not None:
        mean_values = np.mean(background_data, axis=0)
    else:
        mean_values = np.zeros(instance.shape[1])

    shap_values = coefficients * (instance[0] - mean_values)
    return shap_values


def compute_deep_shap(model: Any, instance: np.ndarray) -> np.ndarray:
    """Compute SHAP values for deep learning models.

    This uses gradient-based approximation (similar to Integrated Gradients).

    Args:
        model: Deep learning model.
        instance: Instance as numpy array.

    Returns:
        Array of SHAP values.
    """
    if hasattr(model, "get_gradients"):
        gradients = model.get_gradients(instance)
    else:
        logger.debug("Using finite difference gradients")
        gradients = compute_finite_difference_gradients(model, instance)

    shap_values = gradients * instance[0]
    return shap_values


def compute_finite_difference_gradients(
    model: Any, instance: np.ndarray
) -> np.ndarray:
    """Compute gradients using finite differences.

    Args:
        model: The model.
        instance: Instance as numpy array.

    Returns:
        Array of gradients.
    """
    num_features = instance.shape[1]
    gradients = np.zeros(num_features)

    base_pred = get_prediction(model, instance)
    epsilon = 0.01

    for i in range(num_features):
        perturbed = instance.copy()
        perturbed[0, i] += epsilon

        perturbed_pred = get_prediction(model, perturbed)
        gradients[i] = (perturbed_pred - base_pred) / epsilon

    return gradients
