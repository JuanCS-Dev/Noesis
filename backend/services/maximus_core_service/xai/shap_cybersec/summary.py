"""SHAP Summary Generation.

Functions for generating human-readable summaries and visualizations.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ..base import DetailLevel, FeatureImportance


def generate_summary(
    top_features: list[FeatureImportance],
    prediction: Any,
    shap_values: np.ndarray,
    detail_level: DetailLevel,
) -> str:
    """Generate human-readable summary.

    Args:
        top_features: Top important features.
        prediction: Model prediction.
        shap_values: All SHAP values.
        detail_level: Detail level.

    Returns:
        Summary string.
    """
    base_value = np.mean(shap_values) if len(shap_values) > 0 else 0.0

    if detail_level == DetailLevel.SUMMARY:
        return _generate_summary_brief(top_features, prediction)
    if detail_level == DetailLevel.DETAILED:
        return _generate_summary_detailed(top_features, prediction, base_value)
    return _generate_summary_technical(top_features, prediction, base_value)


def _generate_summary_brief(
    top_features: list[FeatureImportance], prediction: Any
) -> str:
    """Generate brief summary."""
    if not top_features:
        return f"Prediction: {prediction}. No significant features identified."

    top_feature = top_features[0]
    direction = "increases" if top_feature.importance > 0 else "decreases"

    return (
        f"Prediction: {prediction}. "
        f"The most important factor is {top_feature.feature_name} "
        f"which {direction} the prediction by {abs(top_feature.importance):.3f}."
    )


def _generate_summary_detailed(
    top_features: list[FeatureImportance],
    prediction: Any,
    base_value: float,
) -> str:
    """Generate detailed summary."""
    summary_parts = [f"Prediction: {prediction} (base value: {base_value:.3f})."]

    positive_features = [f for f in top_features if f.importance > 0][:3]
    negative_features = [f for f in top_features if f.importance < 0][:3]

    if positive_features:
        contrib_sum = sum(f.importance for f in positive_features)
        features_str = ", ".join(
            [f"{f.feature_name} (+{f.importance:.3f})" for f in positive_features]
        )
        summary_parts.append(
            f"Factors increasing prediction (total: +{contrib_sum:.3f}): "
            f"{features_str}."
        )

    if negative_features:
        contrib_sum = sum(abs(f.importance) for f in negative_features)
        features_str = ", ".join(
            [f"{f.feature_name} ({f.importance:.3f})" for f in negative_features]
        )
        summary_parts.append(
            f"Factors decreasing prediction (total: -{contrib_sum:.3f}): "
            f"{features_str}."
        )

    return " ".join(summary_parts)


def _generate_summary_technical(
    top_features: list[FeatureImportance],
    prediction: Any,
    base_value: float,
) -> str:
    """Generate technical summary."""
    summary_parts = [f"SHAP Explanation for prediction: {prediction}"]
    summary_parts.append(f"Base value: {base_value:.4f}")
    summary_parts.append("Prediction = Base + Sum(SHAP values)")
    summary_parts.append(
        f"\nTop {len(top_features)} features by absolute SHAP value:"
    )

    for i, feature in enumerate(top_features[:15], 1):
        sign = "+" if feature.importance >= 0 else ""
        summary_parts.append(
            f"{i}. {feature.feature_name}: {sign}{feature.importance:.4f} "
            f"(value: {feature.value})"
        )

    return "\n".join(summary_parts)


def calculate_explanation_confidence(
    shap_values: np.ndarray, prediction: Any
) -> float:
    """Calculate confidence in explanation based on additivity.

    Args:
        shap_values: SHAP values.
        prediction: Model prediction.

    Returns:
        Confidence score [0, 1].
    """
    if len(shap_values) == 0:
        return 0.0

    abs_shap = np.abs(shap_values)
    total = np.sum(abs_shap)

    if total == 0:
        return 0.5

    probs = abs_shap / total
    epsilon = 1e-10
    entropy = -np.sum(probs * np.log(probs + epsilon))
    max_entropy = np.log(len(shap_values))

    if max_entropy > 0:
        normalized_entropy = entropy / max_entropy
    else:
        normalized_entropy = 0.0

    return float(normalized_entropy)


def generate_visualization_data(
    top_features: list[FeatureImportance],
    prediction: Any,
    shap_values: np.ndarray,
    detail_level: DetailLevel,
) -> dict[str, Any]:
    """Generate data for SHAP waterfall visualization.

    Args:
        top_features: Top features.
        prediction: Prediction.
        shap_values: All SHAP values.
        detail_level: Detail level.

    Returns:
        Visualization data dict.
    """
    base_value = np.mean(shap_values) if len(shap_values) > 0 else 0.0

    waterfall_data = []
    cumulative = base_value

    for feature in top_features:
        waterfall_data.append({
            "feature": feature.feature_name,
            "shap_value": feature.importance,
            "feature_value": str(feature.value),
            "cumulative_before": cumulative,
            "cumulative_after": cumulative + feature.importance,
        })
        cumulative += feature.importance

    return {
        "type": "shap_waterfall",
        "base_value": float(base_value),
        "prediction": (
            float(prediction)
            if isinstance(prediction, (int, float, np.number))
            else str(prediction)
        ),
        "waterfall_data": waterfall_data,
        "features": [
            {
                "name": f.feature_name,
                "shap_value": f.importance,
                "value": str(f.value),
            }
            for f in top_features
        ],
    }
