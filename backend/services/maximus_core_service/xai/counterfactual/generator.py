"""Counterfactual Explanation Generator.

Main CounterfactualGenerator class for cybersecurity models.

Author: Juan Carlos de Souza
Date: 2025-10-06
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from ..base import (
    DetailLevel,
    ExplainerBase,
    ExplanationResult,
    ExplanationType,
    FeatureImportance,
)
from .config import CounterfactualConfig
from .constraints import init_feature_constraints
from .formatting import (
    calculate_counterfactual_confidence,
    create_no_counterfactual_result,
    generate_counterfactual_summary,
    generate_visualization_data,
)
from .perturbation import generate_counterfactual_candidates
from .selection import identify_changed_features, select_best_counterfactual
from .utils import determine_desired_outcome, dict_to_array

logger = logging.getLogger(__name__)


class CounterfactualGenerator(ExplainerBase):
    """Generate counterfactual explanations for cybersecurity predictions.

    Generates minimal modifications to instances that would flip the prediction,
    helping operators understand decision boundaries and actionable interventions.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize CounterfactualGenerator.

        Args:
            config: Configuration dictionary with counterfactual settings
        """
        super().__init__(config)

        cfg = self.config

        self.cf_config = CounterfactualConfig(
            desired_outcome=cfg.get("desired_outcome", None),
            max_iterations=cfg.get("max_iterations", 1000),
            num_candidates=cfg.get("num_candidates", 10),
            proximity_weight=cfg.get("proximity_weight", 1.0),
            sparsity_weight=cfg.get("sparsity_weight", 0.5),
            validity_weight=cfg.get("validity_weight", 0.3),
        )

        self.feature_constraints = init_feature_constraints()

        logger.info(
            f"CounterfactualGenerator initialized with "
            f"{self.cf_config.num_candidates} candidates"
        )

    async def explain(
        self,
        model: Any,
        instance: dict[str, Any],
        prediction: Any,
        detail_level: DetailLevel = DetailLevel.DETAILED,
    ) -> ExplanationResult:
        """Generate counterfactual explanation.

        Args:
            model: The model being explained
            instance: The input instance (dict of features)
            prediction: The model's prediction for this instance
            detail_level: Level of detail for the explanation

        Returns:
            ExplanationResult with counterfactual scenario
        """
        explain_start = time.time()

        self.validate_instance(instance)

        if not hasattr(model, "predict") and not hasattr(model, "predict_proba"):
            raise ValueError("Model must have 'predict' or 'predict_proba' method")

        explanation_id = str(uuid.uuid4())
        decision_id = instance.get("decision_id", str(uuid.uuid4()))

        desired_outcome = determine_desired_outcome(
            prediction, self.cf_config.desired_outcome
        )

        logger.debug(f"Generating counterfactual: {prediction} → {desired_outcome}")

        feature_names, instance_array = dict_to_array(instance)

        logger.debug(
            f"Generating {self.cf_config.num_candidates} counterfactual candidates"
        )
        candidates = generate_counterfactual_candidates(
            model,
            instance_array,
            feature_names,
            desired_outcome,
            self.feature_constraints,
            self.cf_config.num_candidates,
        )

        if not candidates:
            logger.warning("No valid counterfactuals found")
            return create_no_counterfactual_result(
                explanation_id,
                decision_id,
                prediction,
                detail_level,
                int((time.time() - explain_start) * 1000),
            )

        best_cf, cf_prediction, distance = select_best_counterfactual(
            candidates, instance_array, model
        )

        changed_features = identify_changed_features(
            instance, best_cf, feature_names, instance_array[0]
        )

        all_features = []
        for feature_info in changed_features:
            all_features.append(
                FeatureImportance(
                    feature_name=feature_info["name"],
                    importance=feature_info["importance"],
                    value=feature_info["new_value"],
                    description=feature_info["description"],
                    contribution=feature_info["importance"],
                )
            )

        all_features.sort(key=lambda x: abs(x.importance), reverse=True)

        num_top_features = {
            DetailLevel.SUMMARY: 3,
            DetailLevel.DETAILED: len(all_features),
            DetailLevel.TECHNICAL: len(all_features),
        }.get(detail_level, len(all_features))

        top_features = all_features[:num_top_features]

        summary, counterfactual_text = generate_counterfactual_summary(
            changed_features, prediction, cf_prediction, detail_level
        )

        confidence = calculate_counterfactual_confidence(
            distance, len(changed_features)
        )

        visualization_data = generate_visualization_data(
            changed_features, prediction, cf_prediction
        )

        latency_ms = int((time.time() - explain_start) * 1000)

        logger.info(
            f"Counterfactual generated in {latency_ms}ms (distance: {distance:.3f})"
        )

        return ExplanationResult(
            explanation_id=explanation_id,
            decision_id=decision_id,
            explanation_type=ExplanationType.COUNTERFACTUAL,
            detail_level=detail_level,
            summary=summary,
            top_features=top_features,
            all_features=all_features,
            confidence=confidence,
            counterfactual=counterfactual_text,
            visualization_data=visualization_data,
            model_type=type(model).__name__,
            latency_ms=latency_ms,
            metadata={
                "original_prediction": prediction,
                "counterfactual_prediction": cf_prediction,
                "distance": float(distance),
                "num_changes": len(changed_features),
                "num_candidates_tried": self.cf_config.num_candidates,
            },
        )

    def get_supported_models(self) -> list[str]:
        """Get list of supported model types.

        Returns:
            List of supported model types
        """
        return [
            "sklearn",
            "xgboost",
            "lightgbm",
            "pytorch",
            "tensorflow",
            "custom",
        ]
