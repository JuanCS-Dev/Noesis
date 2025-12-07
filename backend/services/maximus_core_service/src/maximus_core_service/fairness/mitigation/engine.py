"""Mitigation Engine Core.

Main MitigationEngine class integrating all mitigation strategies.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from ..base import FairnessException, MitigationResult
from ..constraints import FairnessConstraints
from .calibration import CalibrationMixin
from .helpers import HelpersMixin
from .reweighing import ReweighingMixin
from .threshold import ThresholdMixin

logger = logging.getLogger(__name__)


class MitigationEngine(
    ReweighingMixin,
    ThresholdMixin,
    CalibrationMixin,
    HelpersMixin,
):
    """Bias mitigation engine for cybersecurity AI models.

    Implements multiple mitigation strategies to reduce bias while
    maintaining acceptable model performance.

    Attributes:
        fairness_constraints: FairnessConstraints instance for evaluation
        performance_threshold: Minimum acceptable performance after mitigation
        fairness_improvement_threshold: Minimum fairness improvement required
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize MitigationEngine.

        Args:
            config: Configuration dictionary
        """
        config = config or {}

        self.fairness_constraints = FairnessConstraints(
            config.get("fairness_config", {})
        )

        self.performance_threshold = config.get("performance_threshold", 0.75)
        self.max_performance_loss = config.get("max_performance_loss", 0.05)

        self.fairness_improvement_threshold = config.get(
            "fairness_improvement_threshold", 0.05
        )

        self.mitigation_strategies = config.get(
            "mitigation_strategies",
            ["threshold_optimization", "reweighing", "calibration_adjustment"],
        )

        logger.info(
            f"MitigationEngine initialized with {len(self.mitigation_strategies)} "
            f"strategies, performance_threshold={self.performance_threshold}"
        )

    def mitigate_auto(
        self,
        predictions: np.ndarray,
        true_labels: np.ndarray,
        protected_attribute: np.ndarray,
        protected_value: Any = 1,
        X_train: np.ndarray | None = None,
        y_train: np.ndarray | None = None,
        model: Any | None = None,
    ) -> MitigationResult:
        """Automatically select and apply best mitigation strategy.

        Tries multiple strategies and returns the best result.

        Args:
            predictions: Model predictions
            true_labels: True labels
            protected_attribute: Protected attribute values
            protected_value: Value indicating protected group
            X_train: Training features (for reweighing)
            y_train: Training labels (for reweighing)
            model: Model (for reweighing)

        Returns:
            Best MitigationResult
        """
        logger.info("Starting automatic mitigation strategy selection...")

        results = []

        for strategy in self.mitigation_strategies:
            try:
                if strategy == "threshold_optimization":
                    result = self.mitigate_threshold_optimization(
                        predictions, true_labels, protected_attribute, protected_value
                    )
                    results.append(result)

                elif strategy == "calibration_adjustment":
                    result = self.mitigate_calibration_adjustment(
                        predictions, true_labels, protected_attribute, protected_value
                    )
                    results.append(result)

                elif (
                    strategy == "reweighing"
                    and X_train is not None
                    and model is not None
                ):
                    result = self.mitigate_reweighing(
                        X_train, y_train, protected_attribute, protected_value, model
                    )
                    results.append(result)

            except Exception as e:
                logger.error(f"Strategy {strategy} failed: {e}")
                continue

        if not results:
            raise FairnessException("All mitigation strategies failed")

        best_result = self._select_best_result(results)

        logger.info(
            f"Auto mitigation complete: selected {best_result.mitigation_method}, "
            f"success={best_result.success}"
        )

        return best_result
