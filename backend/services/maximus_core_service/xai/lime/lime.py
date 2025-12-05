"""CyberSecLIME - Main LIME Explainer.

LIME adapted for cybersecurity threat classification.
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
from .config import PerturbationConfig
from .explanation import ExplanationMixin
from .interpretable import InterpretableMixin
from .perturbation import PerturbationMixin

logger = logging.getLogger(__name__)


class CyberSecLIME(
    PerturbationMixin,
    InterpretableMixin,
    ExplanationMixin,
    ExplainerBase,
):
    """LIME explainer adapted for cybersecurity models.

    Supports:
        - Network traffic classification
        - Threat scoring models
        - Behavioral anomaly detection
        - Narrative manipulation detection
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize CyberSecLIME.

        Args:
            config: Configuration dictionary with perturbation settings
        """
        super().__init__(config)

        cfg = self.config

        self.perturbation_config = PerturbationConfig(
            num_samples=cfg.get("num_samples", 5000),
            feature_selection=cfg.get("feature_selection", "auto"),
            kernel_width=cfg.get("kernel_width", 0.25),
            sample_around_instance=cfg.get("sample_around_instance", True),
        )

        self.feature_handlers = {
            "numeric": self._perturb_numeric,
            "categorical": self._perturb_categorical,
            "ip_address": self._perturb_ip,
            "port": self._perturb_port,
            "score": self._perturb_score,
            "text": self._perturb_text,
        }

        logger.info(
            f"CyberSecLIME initialized with "
            f"{self.perturbation_config.num_samples} samples"
        )

    async def explain(
        self,
        model: Any,
        instance: dict[str, Any],
        prediction: Any,
        detail_level: DetailLevel = DetailLevel.DETAILED,
    ) -> ExplanationResult:
        """Generate LIME explanation for a cybersecurity prediction.

        Args:
            model: The model being explained
            instance: The input instance (dict of features)
            prediction: The model's prediction for this instance
            detail_level: Level of detail for the explanation

        Returns:
            ExplanationResult with feature importances
        """
        explain_start = time.time()

        self.validate_instance(instance)

        if not hasattr(model, "predict") and not hasattr(model, "predict_proba"):
            raise ValueError("Model must have 'predict' or 'predict_proba' method")

        explanation_id = str(uuid.uuid4())
        decision_id = instance.get("decision_id", str(uuid.uuid4()))

        feature_types = self._infer_feature_types(instance)

        logger.debug(
            f"Generating {self.perturbation_config.num_samples} perturbed samples"
        )
        perturbed_samples, distances = self._generate_perturbed_samples(
            instance, feature_types, self.perturbation_config.num_samples
        )

        logger.debug(f"Getting predictions for {len(perturbed_samples)} samples")
        predictions = self._get_model_predictions(model, perturbed_samples)

        weights = self._calculate_kernel_weights(
            distances, self.perturbation_config.kernel_width
        )

        logger.debug("Fitting interpretable model")
        feature_importances = self._fit_interpretable_model(
            perturbed_samples, predictions, weights, feature_types.keys()
        )

        sorted_features = sorted(
            [(k, v) for k, v in feature_importances.items() if k != "__intercept__"],
            key=lambda x: abs(x[1]),
            reverse=True,
        )

        all_features = []
        for feature_name, importance in sorted_features:
            feature_value = instance.get(feature_name)
            description = self.format_feature_description(feature_name, feature_value)

            all_features.append(
                FeatureImportance(
                    feature_name=feature_name,
                    importance=importance,
                    value=feature_value,
                    description=description,
                    contribution=importance,
                )
            )

        num_top_features = {
            DetailLevel.SUMMARY: 3,
            DetailLevel.DETAILED: 10,
            DetailLevel.TECHNICAL: len(all_features),
        }.get(detail_level, 10)

        top_features = all_features[:num_top_features]

        summary = self._generate_summary(top_features, prediction, detail_level)

        confidence = self._calculate_explanation_confidence(
            predictions,
            self._predict_interpretable_model(perturbed_samples, feature_importances),
            weights,
        )

        visualization_data = self._generate_visualization_data(
            top_features, prediction, detail_level
        )

        latency_ms = int((time.time() - explain_start) * 1000)

        logger.info(
            f"LIME explanation generated in {latency_ms}ms "
            f"(confidence: {confidence:.2f})"
        )

        return ExplanationResult(
            explanation_id=explanation_id,
            decision_id=decision_id,
            explanation_type=ExplanationType.LIME,
            detail_level=detail_level,
            summary=summary,
            top_features=top_features,
            all_features=all_features,
            confidence=confidence,
            visualization_data=visualization_data,
            model_type=type(model).__name__,
            latency_ms=latency_ms,
            metadata={
                "num_samples": self.perturbation_config.num_samples,
                "num_features": len(all_features),
                "prediction": prediction,
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
