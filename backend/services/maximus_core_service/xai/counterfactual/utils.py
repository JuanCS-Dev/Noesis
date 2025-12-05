"""Utility functions for counterfactual generation.

Conversion, prediction, and outcome matching utilities.

Author: Juan Carlos de Souza
Date: 2025-10-06
"""

from __future__ import annotations

from typing import Any

import numpy as np


def dict_to_array(instance: dict[str, Any]) -> tuple[list[str], np.ndarray]:
    """Convert instance dict to numpy array.

    Args:
        instance: Instance dictionary

    Returns:
        Tuple of (feature_names, feature_array)
    """
    meta_fields = {"decision_id", "timestamp", "analysis_id"}
    feature_names = sorted([k for k in instance if k not in meta_fields])

    feature_values = []
    for name in feature_names:
        value = instance.get(name, 0)

        if isinstance(value, (int, float)) or isinstance(value, bool):
            feature_values.append(float(value))
        elif isinstance(value, str):
            feature_values.append(float(hash(value) % 1000000) / 1000000.0)
        else:
            feature_values.append(0.0)

    return feature_names, np.array(feature_values).reshape(1, -1)


def get_prediction(model: Any, instance: np.ndarray) -> float:
    """Get model prediction.

    Args:
        model: The model
        instance: Instance array

    Returns:
        Prediction value
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


def matches_desired_outcome(prediction: float, desired_outcome: Any) -> bool:
    """Check if prediction matches desired outcome.

    Args:
        prediction: Model prediction
        desired_outcome: Desired outcome

    Returns:
        True if matches
    """
    if isinstance(desired_outcome, (int, float, np.number)):
        return abs(prediction - float(desired_outcome)) < 0.1

    return prediction == desired_outcome


def determine_desired_outcome(
    current_prediction: Any,
    config_desired_outcome: Any | None,
) -> Any:
    """Determine desired counterfactual outcome.

    Args:
        current_prediction: Current prediction
        config_desired_outcome: Configured desired outcome (if any)

    Returns:
        Desired outcome
    """
    if config_desired_outcome is not None:
        return config_desired_outcome

    if isinstance(current_prediction, bool):
        return not current_prediction

    if isinstance(current_prediction, (int, float, np.number)):
        if 0 <= current_prediction <= 1:
            return 1.0 - current_prediction
        if current_prediction in [0, 1]:
            return 1 - current_prediction

    if isinstance(current_prediction, str):
        flip_map = {
            "BLOCK": "ALLOW",
            "ALLOW": "BLOCK",
            "REJECTED": "APPROVED",
            "APPROVED": "REJECTED",
            "HIGH": "LOW",
            "LOW": "HIGH",
        }
        return flip_map.get(current_prediction.upper(), "OPPOSITE")

    return "OPPOSITE"
