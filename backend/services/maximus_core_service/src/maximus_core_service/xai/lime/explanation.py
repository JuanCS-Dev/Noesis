"""Explanation Generation for LIME.

Summary and visualization generation.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ..base import DetailLevel, FeatureImportance


class ExplanationMixin:
    """Mixin providing explanation generation methods."""

    def _generate_summary(
        self,
        top_features: list[FeatureImportance],
        prediction: Any,
        detail_level: DetailLevel,
    ) -> str:
        """Generate human-readable summary.

        Args:
            top_features: Top important features
            prediction: Model prediction
            detail_level: Detail level

        Returns:
            Summary string
        """
        if detail_level == DetailLevel.SUMMARY:
            if not top_features:
                return f"Prediction: {prediction}. No significant features identified."

            top_feature = top_features[0]
            direction = "increases" if top_feature.importance > 0 else "decreases"

            return (
                f"Prediction: {prediction}. "
                f"The most important factor is {top_feature.feature_name} "
                f"which {direction} the likelihood of this prediction."
            )

        if detail_level == DetailLevel.DETAILED:
            summary_parts = [f"Prediction: {prediction}."]

            positive_features = [f for f in top_features if f.importance > 0][:2]
            negative_features = [f for f in top_features if f.importance < 0][:2]

            if positive_features:
                features_str = ", ".join([f.feature_name for f in positive_features])
                summary_parts.append(
                    f"Key factors supporting this prediction: {features_str}."
                )

            if negative_features:
                features_str = ", ".join([f.feature_name for f in negative_features])
                summary_parts.append(
                    f"Key factors against this prediction: {features_str}."
                )

            return " ".join(summary_parts)

        # TECHNICAL
        summary_parts = [f"LIME Explanation for prediction: {prediction}"]
        summary_parts.append(f"Top {len(top_features)} features by importance:")

        for i, feature in enumerate(top_features[:10], 1):
            direction = "+" if feature.importance >= 0 else "-"
            summary_parts.append(
                f"{i}. {feature.feature_name}: {direction}"
                f"{abs(feature.importance):.4f} (value: {feature.value})"
            )

        return "\n".join(summary_parts)

    def _generate_visualization_data(
        self,
        top_features: list[FeatureImportance],
        prediction: Any,
        detail_level: DetailLevel,
    ) -> dict[str, Any]:
        """Generate data for visualization.

        Args:
            top_features: Top features
            prediction: Prediction
            detail_level: Detail level

        Returns:
            Visualization data dict
        """
        return {
            "type": "lime_bar_chart",
            "prediction": (
                float(prediction)
                if isinstance(prediction, (int, float, np.number))
                else str(prediction)
            ),
            "features": [
                {
                    "name": f.feature_name,
                    "importance": f.importance,
                    "value": str(f.value),
                }
                for f in top_features
            ],
        }
