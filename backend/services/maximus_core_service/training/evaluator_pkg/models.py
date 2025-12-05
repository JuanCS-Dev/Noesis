"""Models for model evaluator module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class EvaluationMetrics:
    """Evaluation metrics for a model."""

    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float | None = None
    pr_auc: float | None = None
    confusion_matrix: np.ndarray | None = None
    per_class_metrics: dict[int, dict[str, float]] | None = None
    avg_inference_time_ms: float | None = None
    throughput_samples_per_sec: float | None = None
    additional_metrics: dict[str, float] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "accuracy": float(self.accuracy),
            "precision": float(self.precision),
            "recall": float(self.recall),
            "f1_score": float(self.f1_score),
        }

        if self.roc_auc is not None:
            result["roc_auc"] = float(self.roc_auc)
        if self.pr_auc is not None:
            result["pr_auc"] = float(self.pr_auc)
        if self.confusion_matrix is not None:
            result["confusion_matrix"] = self.confusion_matrix.tolist()
        if self.per_class_metrics is not None:
            result["per_class_metrics"] = self.per_class_metrics
        if self.avg_inference_time_ms is not None:
            result["avg_inference_time_ms"] = float(self.avg_inference_time_ms)
        if self.throughput_samples_per_sec is not None:
            result["throughput_samples_per_sec"] = float(self.throughput_samples_per_sec)
        if self.additional_metrics:
            result["additional_metrics"] = self.additional_metrics

        return result
