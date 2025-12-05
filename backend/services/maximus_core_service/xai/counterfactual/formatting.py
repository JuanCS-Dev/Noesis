"""Formatting functions for counterfactual explanations.

Summary generation, visualization data, and confidence calculation.

Author: Juan Carlos de Souza
Date: 2025-10-06
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ..base import (
    DetailLevel,
    ExplanationResult,
    ExplanationType,
    FeatureImportance,
)


def generate_counterfactual_summary(
    changed_features: list[dict[str, Any]],
    original_pred: Any,
    cf_pred: float,
    detail_level: DetailLevel,
) -> tuple[str, str]:
    """Generate counterfactual summary and text.

    Args:
        changed_features: Changed features
        original_pred: Original prediction
        cf_pred: Counterfactual prediction
        detail_level: Detail level

    Returns:
        Tuple of (summary, counterfactual_text)
    """
    if not changed_features:
        summary = f"No counterfactual found. Original prediction: {original_pred}"
        cf_text = "Unable to generate alternative scenario."
        return summary, cf_text

    if detail_level == DetailLevel.SUMMARY:
        top_change = changed_features[0]
        summary = (
            f"If {top_change['name']} were changed from "
            f"{top_change['original_value']:.2f} to {top_change['new_value']:.2f}, "
            f"prediction would be {cf_pred:.2f}."
        )
        cf_text = summary

    elif detail_level == DetailLevel.DETAILED:
        summary_parts = [
            f"Original prediction: {original_pred}, Counterfactual: {cf_pred}"
        ]

        if len(changed_features) == 1:
            change = changed_features[0]
            summary_parts.append(
                f"If {change['name']} changed from {change['original_value']:.2f} "
                f"to {change['new_value']:.2f}, prediction would flip."
            )
        else:
            summary_parts.append(f"Required {len(changed_features)} changes:")
            for change in changed_features[:5]:
                summary_parts.append(
                    f"  - {change['name']}: {change['original_value']:.2f} "
                    f"→ {change['new_value']:.2f}"
                )

        summary = " ".join(summary_parts)
        cf_text = summary

    else:  # TECHNICAL
        summary_parts = ["Counterfactual Explanation"]
        summary_parts.append(f"Original prediction: {original_pred}")
        summary_parts.append(f"Counterfactual prediction: {cf_pred}")
        summary_parts.append(f"\nRequired changes ({len(changed_features)} features):")

        for i, change in enumerate(changed_features, 1):
            delta = change["new_value"] - change["original_value"]
            summary_parts.append(
                f"{i}. {change['name']}: {change['original_value']:.4f} → "
                f"{change['new_value']:.4f} (Δ={delta:.4f})"
            )

        summary = "\n".join(summary_parts)
        cf_text = summary

    return summary, cf_text


def calculate_counterfactual_confidence(distance: float, num_changes: int) -> float:
    """Calculate confidence in counterfactual.

    Args:
        distance: Distance from original
        num_changes: Number of features changed

    Returns:
        Confidence score [0, 1]
    """
    distance_factor = np.exp(-distance)
    sparsity_factor = 1.0 / (1.0 + num_changes)

    confidence = 0.6 * distance_factor + 0.4 * sparsity_factor

    return max(0.0, min(1.0, confidence))


def generate_visualization_data(
    changed_features: list[dict[str, Any]],
    original_pred: Any,
    cf_pred: float,
) -> dict[str, Any]:
    """Generate visualization data.

    Args:
        changed_features: Changed features
        original_pred: Original prediction
        cf_pred: Counterfactual prediction

    Returns:
        Visualization data dict
    """
    return {
        "type": "counterfactual_comparison",
        "original_prediction": (
            float(original_pred)
            if isinstance(original_pred, (int, float, np.number))
            else str(original_pred)
        ),
        "counterfactual_prediction": float(cf_pred),
        "changes": [
            {
                "feature": change["name"],
                "original": float(change["original_value"]),
                "counterfactual": float(change["new_value"]),
                "delta": float(change["new_value"] - change["original_value"]),
            }
            for change in changed_features
        ],
    }


def create_no_counterfactual_result(
    explanation_id: str,
    decision_id: str,
    prediction: Any,
    detail_level: DetailLevel,
    latency_ms: int,
) -> ExplanationResult:
    """Create result when no counterfactual is found.

    Args:
        explanation_id: Explanation ID
        decision_id: Decision ID
        prediction: Original prediction
        detail_level: Detail level
        latency_ms: Latency

    Returns:
        ExplanationResult
    """
    dummy_feature = FeatureImportance(
        feature_name="no_counterfactual",
        importance=0.0,
        value=None,
        description="No counterfactual found within constraints",
        contribution=0.0,
    )

    return ExplanationResult(
        explanation_id=explanation_id,
        decision_id=decision_id,
        explanation_type=ExplanationType.COUNTERFACTUAL,
        detail_level=detail_level,
        summary=f"No counterfactual found. Original prediction: {prediction}",
        top_features=[dummy_feature],
        all_features=[dummy_feature],
        confidence=0.0,
        counterfactual="Unable to generate alternative scenario within constraints.",
        visualization_data={"type": "no_counterfactual"},
        model_type="unknown",
        latency_ms=latency_ms,
        metadata={"original_prediction": prediction},
    )
