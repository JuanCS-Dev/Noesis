"""Selection functions for counterfactual generation.

Best counterfactual selection and changed feature identification.

Author: Juan Carlos de Souza
Date: 2025-10-06
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .utils import get_prediction


def select_best_counterfactual(
    candidates: list[np.ndarray],
    original: np.ndarray,
    model: Any,
) -> tuple[np.ndarray, float, float]:
    """Select best counterfactual (closest to original).

    Args:
        candidates: List of candidate arrays
        original: Original instance
        model: The model

    Returns:
        Tuple of (best_candidate, prediction, distance)
    """
    best_cf = candidates[0]
    best_distance = float("inf")
    best_prediction = get_prediction(model, best_cf.reshape(1, -1))

    for candidate in candidates:
        distance = np.linalg.norm(candidate - original[0])

        if distance < best_distance:
            best_distance = distance
            best_cf = candidate
            best_prediction = get_prediction(model, candidate.reshape(1, -1))

    return best_cf, best_prediction, best_distance


def identify_changed_features(
    original_dict: dict[str, Any],
    counterfactual: np.ndarray,
    feature_names: list[str],
    original_array: np.ndarray,
) -> list[dict[str, Any]]:
    """Identify which features changed in counterfactual.

    Args:
        original_dict: Original instance dict
        counterfactual: Counterfactual array
        feature_names: Feature names
        original_array: Original array

    Returns:
        List of changed feature info dicts
    """
    changed_features = []

    for i, feature_name in enumerate(feature_names):
        original_value = original_array[i]
        cf_value = counterfactual[i]

        if abs(cf_value - original_value) > 0.01:
            change_magnitude = cf_value - original_value
            dict_value = original_dict.get(feature_name, original_value)

            changed_features.append(
                {
                    "name": feature_name,
                    "original_value": original_value,
                    "new_value": cf_value,
                    "importance": abs(change_magnitude),
                    "description": _format_change_description(
                        feature_name, dict_value, cf_value, change_magnitude
                    ),
                }
            )

    return changed_features


def _format_change_description(
    feature_name: str,
    original: Any,
    new_value: float,
    change: float,
) -> str:
    """Format change description.

    Args:
        feature_name: Feature name
        original: Original value
        new_value: New value
        change: Change magnitude

    Returns:
        Human-readable description
    """
    direction = "increase" if change > 0 else "decrease"
    return (
        f"{feature_name}: {original:.2f} → {new_value:.2f} "
        f"({direction} of {abs(change):.2f})"
    )
