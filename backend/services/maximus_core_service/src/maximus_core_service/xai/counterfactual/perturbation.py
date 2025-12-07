"""Perturbation functions for counterfactual generation.

Random and gradient-based perturbation strategies.

Author: Juan Carlos de Souza
Date: 2025-10-06
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .constraints import apply_constraints
from .utils import get_prediction, matches_desired_outcome


def perturb_feature(
    feature_name: str,
    original_value: float,
    feature_constraints: dict[str, dict[str, Any]],
) -> float:
    """Perturb a single feature while respecting constraints.

    Args:
        feature_name: Feature name
        original_value: Original value
        feature_constraints: Feature constraints dictionary

    Returns:
        Perturbed value
    """
    constraints = None
    for pattern, constraint in feature_constraints.items():
        if pattern in feature_name.lower():
            constraints = constraint
            break

    if constraints:
        min_val = constraints["min"]
        max_val = constraints["max"]

        if constraints["type"] == "int":
            return float(np.random.randint(min_val, max_val + 1))
        return np.random.uniform(min_val, max_val)

    std = max(abs(original_value) * 0.3, 0.2)
    perturbed = original_value + np.random.normal(0, std)

    if any(
        keyword in feature_name.lower()
        for keyword in ["count", "size", "length", "num_"]
    ):
        perturbed = max(0, perturbed)

    return perturbed


def generate_random_perturbation(
    instance: np.ndarray,
    feature_names: list[str],
    feature_constraints: dict[str, dict[str, Any]],
) -> np.ndarray:
    """Generate random perturbation of instance.

    Args:
        instance: Original instance
        feature_names: Feature names
        feature_constraints: Feature constraints dictionary

    Returns:
        Perturbed instance
    """
    perturbed = instance.copy()

    num_to_perturb = np.random.randint(1, min(4, len(feature_names) + 1))
    features_to_perturb = np.random.choice(
        len(feature_names), num_to_perturb, replace=False
    )

    for idx in features_to_perturb:
        feature_name = feature_names[idx]
        original_value = instance[0, idx]

        new_value = perturb_feature(feature_name, original_value, feature_constraints)
        perturbed[0, idx] = new_value

    return perturbed


def compute_gradients(model: Any, instance: np.ndarray) -> np.ndarray:
    """Compute gradients using finite differences.

    Args:
        model: The model
        instance: Instance array

    Returns:
        Gradient array
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


def generate_gradient_based_cf(
    model: Any,
    instance: np.ndarray,
    desired_outcome: Any,
    feature_names: list[str],
    feature_constraints: dict[str, dict[str, Any]],
) -> np.ndarray | None:
    """Generate counterfactual using gradient descent.

    Args:
        model: The model
        instance: Instance array
        desired_outcome: Desired outcome
        feature_names: Feature names
        feature_constraints: Feature constraints dictionary

    Returns:
        Counterfactual array or None
    """
    candidate = instance.copy()
    current_pred = get_prediction(model, candidate)

    if isinstance(desired_outcome, (int, float, np.number)):
        target_value = float(desired_outcome)
    else:
        target_value = 1.0 - current_pred if 0 <= current_pred <= 1 else 0.5

    learning_rate = 0.1
    max_steps = 50

    for _ in range(max_steps):
        gradients = compute_gradients(model, candidate)

        direction = target_value - current_pred
        candidate += learning_rate * direction * gradients.reshape(1, -1)

        for i, feature_name in enumerate(feature_names):
            candidate[0, i] = apply_constraints(
                feature_name, candidate[0, i], feature_constraints
            )

        current_pred = get_prediction(model, candidate)

        if matches_desired_outcome(current_pred, desired_outcome):
            return candidate

    return None


def generate_counterfactual_candidates(
    model: Any,
    instance: np.ndarray,
    feature_names: list[str],
    desired_outcome: Any,
    feature_constraints: dict[str, dict[str, Any]],
    num_candidates: int,
) -> list[np.ndarray]:
    """Generate counterfactual candidates using mixed strategies.

    Args:
        model: The model
        instance: Instance as numpy array (1 x M)
        feature_names: Feature names
        desired_outcome: Desired prediction
        feature_constraints: Feature constraints dictionary
        num_candidates: Number of candidates to generate

    Returns:
        List of counterfactual candidate arrays
    """
    candidates = []

    # Strategy 1: Random perturbations (50% of candidates)
    num_random = num_candidates // 2

    for _ in range(num_random):
        candidate = generate_random_perturbation(
            instance, feature_names, feature_constraints
        )

        pred = get_prediction(model, candidate)

        if matches_desired_outcome(pred, desired_outcome):
            candidates.append(candidate[0])

    # Strategy 2: Gradient-based (if model supports)
    if hasattr(model, "predict_proba") and len(candidates) < num_candidates:
        num_gradient = num_candidates - len(candidates)

        for _ in range(num_gradient):
            candidate = generate_gradient_based_cf(
                model, instance, desired_outcome, feature_names, feature_constraints
            )

            if candidate is not None:
                pred = get_prediction(model, candidate)
                if matches_desired_outcome(pred, desired_outcome):
                    candidates.append(candidate[0])

    return candidates
