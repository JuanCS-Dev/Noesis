"""CyberSecSHAP Explainer.

SHAP explainer adapted for cybersecurity models.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

import numpy as np

from ..base import (
    DetailLevel,
    ExplainerBase,
    ExplanationResult,
    ExplanationType,
    FeatureImportance,
)
from .algorithms import (
    compute_deep_shap,
    compute_kernel_shap,
    compute_linear_shap,
    compute_tree_shap,
)
from .config import SHAPConfig
from .summary import (
    calculate_explanation_confidence,
    generate_summary,
    generate_visualization_data,
)

logger = logging.getLogger(__name__)


class CyberSecSHAP(ExplainerBase):
    """SHAP explainer adapted for cybersecurity models.

    Supports:
        - Tree-based models (XGBoost, LightGBM, Random Forest)
        - Neural networks (PyTorch, TensorFlow)
        - Linear models (Logistic Regression, SVM)
        - Model-agnostic kernel SHAP for any model

    Attributes:
        shap_config: SHAP configuration.
        background_data: Background dataset for kernel SHAP.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize CyberSecSHAP.

        Args:
            config: Configuration dictionary with SHAP settings.
        """
        super().__init__(config)

        cfg = self.config

        self.shap_config = SHAPConfig(
            algorithm=cfg.get("algorithm", "kernel"),
            num_background_samples=cfg.get("num_background_samples", 100),
            num_features=cfg.get("num_features", None),
            check_additivity=cfg.get("check_additivity", False),
        )

        self.background_data: np.ndarray | None = None

        logger.info(
            f"CyberSecSHAP initialized with algorithm={self.shap_config.algorithm}"
        )

    async def explain(
        self,
        model: Any,
        instance: dict[str, Any],
        prediction: Any,
        detail_level: DetailLevel = DetailLevel.DETAILED,
    ) -> ExplanationResult:
        """Generate SHAP explanation for a cybersecurity prediction.

        Args:
            model: The model being explained.
            instance: The input instance (dict of features).
            prediction: The model's prediction for this instance.
            detail_level: Level of detail for the explanation.

        Returns:
            ExplanationResult with SHAP values as feature importances.
        """
        explain_start = time.time()

        self.validate_instance(instance)

        explanation_id = str(uuid.uuid4())
        decision_id = instance.get("decision_id", str(uuid.uuid4()))

        model_type_str = self._detect_model_type(model)
        algorithm = self._select_shap_algorithm(model_type_str)

        logger.debug(
            f"Using SHAP algorithm: {algorithm} for model type: {model_type_str}"
        )

        feature_names, feature_array = self._dict_to_array(instance)

        logger.debug(f"Computing SHAP values for {len(feature_names)} features")
        shap_values = self._compute_shap_values(
            model, feature_array, feature_names, algorithm
        )

        all_features = self._create_feature_importances(
            feature_names, shap_values, instance
        )

        all_features.sort(key=lambda x: abs(x.importance), reverse=True)

        num_top_features = {
            DetailLevel.SUMMARY: 3,
            DetailLevel.DETAILED: 10,
            DetailLevel.TECHNICAL: len(all_features),
        }.get(detail_level, 10)

        top_features = all_features[:num_top_features]

        summary = generate_summary(top_features, prediction, shap_values, detail_level)
        confidence = calculate_explanation_confidence(shap_values, prediction)
        visualization_data = generate_visualization_data(
            top_features, prediction, shap_values, detail_level
        )

        latency_ms = int((time.time() - explain_start) * 1000)

        logger.info(
            f"SHAP explanation generated in {latency_ms}ms "
            f"(confidence: {confidence:.2f})"
        )

        return ExplanationResult(
            explanation_id=explanation_id,
            decision_id=decision_id,
            explanation_type=ExplanationType.SHAP,
            detail_level=detail_level,
            summary=summary,
            top_features=top_features,
            all_features=all_features,
            confidence=confidence,
            visualization_data=visualization_data,
            model_type=model_type_str,
            latency_ms=latency_ms,
            metadata={
                "algorithm": algorithm,
                "num_features": len(all_features),
                "prediction": prediction,
                "base_value": (
                    float(np.mean(shap_values)) if len(shap_values) > 0 else 0.0
                ),
            },
        )

    def get_supported_models(self) -> list[str]:
        """Get list of supported model types.

        Returns:
            List of supported model types.
        """
        return [
            "xgboost",
            "lightgbm",
            "random_forest",
            "gradient_boosting",
            "pytorch",
            "tensorflow",
            "keras",
            "sklearn",
            "linear",
            "custom",
        ]

    def set_background_data(self, background_data: np.ndarray) -> None:
        """Set background dataset for kernel SHAP.

        Args:
            background_data: Background samples (N x M array).
        """
        self.background_data = background_data
        logger.info(f"Background data set: {background_data.shape}")

    def _detect_model_type(self, model: Any) -> str:
        """Detect model type from model object.

        Args:
            model: The model.

        Returns:
            Model type string.
        """
        model_class = type(model).__name__.lower()
        model_module = (
            type(model).__module__.lower()
            if hasattr(type(model), "__module__")
            else ""
        )

        if "xgb" in model_module or "xgboost" in model_class:
            return "xgboost"
        if "lightgbm" in model_module or "lgbm" in model_class:
            return "lightgbm"
        if "randomforest" in model_class:
            return "random_forest"
        if "gradientboosting" in model_class:
            return "gradient_boosting"
        if "torch" in model_module or "pytorch" in model_module:
            return "pytorch"
        if "tensorflow" in model_module or "keras" in model_module:
            return "tensorflow"
        if "linear" in model_class or "logistic" in model_class:
            return "linear"
        if "sklearn" in model_module:
            return "sklearn"
        return "custom"

    def _select_shap_algorithm(self, model_type: str) -> str:
        """Select appropriate SHAP algorithm based on model type.

        Args:
            model_type: Detected model type.

        Returns:
            SHAP algorithm name.
        """
        if self.shap_config.algorithm != "kernel":
            return self.shap_config.algorithm

        if model_type in [
            "xgboost", "lightgbm", "random_forest", "gradient_boosting"
        ]:
            return "tree"
        if model_type in ["pytorch", "tensorflow"]:
            return "deep"
        if model_type == "linear":
            return "linear"
        return "kernel"

    def _dict_to_array(
        self, instance: dict[str, Any]
    ) -> tuple[list[str], np.ndarray]:
        """Convert instance dict to numpy array.

        Args:
            instance: Instance dictionary.

        Returns:
            Tuple of (feature_names, feature_array).
        """
        meta_fields = {"decision_id", "timestamp", "analysis_id"}
        feature_names = sorted([k for k in instance if k not in meta_fields])

        feature_values = []
        for name in feature_names:
            value = instance.get(name, 0)

            if isinstance(value, (int, float, bool)):
                feature_values.append(float(value))
            elif isinstance(value, str):
                feature_values.append(float(hash(value) % 1000000) / 1000000.0)
            else:
                feature_values.append(0.0)

        return feature_names, np.array(feature_values).reshape(1, -1)

    def _compute_shap_values(
        self,
        model: Any,
        instance: np.ndarray,
        feature_names: list[str],
        algorithm: str,
    ) -> np.ndarray:
        """Compute SHAP values using specified algorithm.

        Args:
            model: The model.
            instance: Instance as numpy array (1 x M).
            feature_names: Feature names.
            algorithm: SHAP algorithm to use.

        Returns:
            Array of SHAP values (M,).
        """
        if algorithm == "tree":
            return compute_tree_shap(model, instance)
        if algorithm == "linear":
            return compute_linear_shap(model, instance, self.background_data)
        if algorithm == "deep":
            return compute_deep_shap(model, instance)
        return compute_kernel_shap(
            model, instance, self.background_data, self.shap_config.check_additivity
        )

    def _create_feature_importances(
        self,
        feature_names: list[str],
        shap_values: np.ndarray,
        instance: dict[str, Any],
    ) -> list[FeatureImportance]:
        """Create FeatureImportance objects from SHAP values.

        Args:
            feature_names: Feature names.
            shap_values: SHAP values array.
            instance: Original instance dict.

        Returns:
            List of FeatureImportance objects.
        """
        features = []
        for i, feature_name in enumerate(feature_names):
            shap_value = float(shap_values[i])
            feature_value = instance.get(feature_name)
            description = self.format_feature_description(feature_name, feature_value)

            features.append(
                FeatureImportance(
                    feature_name=feature_name,
                    importance=shap_value,
                    value=feature_value,
                    description=description,
                    contribution=shap_value,
                )
            )
        return features
