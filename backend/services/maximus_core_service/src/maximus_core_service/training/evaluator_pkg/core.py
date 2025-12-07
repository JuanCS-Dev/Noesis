"""Core model evaluator implementation."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from .models import EvaluationMetrics

logger = logging.getLogger(__name__)


class ModelEvaluator:
    """Evaluates trained models on test data."""

    def __init__(
        self,
        model: Any,
        test_features: np.ndarray,
        test_labels: np.ndarray,
        class_names: list[str] | None = None,
    ) -> None:
        """Initialize evaluator."""
        self.model = model
        self.test_features = test_features
        self.test_labels = test_labels
        self.class_names = class_names

        # Filter out unlabeled samples
        labeled_mask = test_labels >= 0
        self.test_features = test_features[labeled_mask]
        self.test_labels = test_labels[labeled_mask]

        self.n_samples = len(self.test_labels)
        self.n_classes = len(np.unique(self.test_labels))

        logger.info("ModelEvaluator initialized: %s samples, %s classes", self.n_samples, self.n_classes)

    def evaluate(
        self,
        compute_roc_auc: bool = True,
        compute_pr_auc: bool = True,
        benchmark_latency: bool = True,
    ) -> EvaluationMetrics:
        """Evaluate model on test data."""
        predictions, probabilities = self._get_predictions()

        accuracy = self._compute_accuracy(predictions)
        precision = self._compute_precision(predictions)
        recall = self._compute_recall(predictions)
        f1 = self._compute_f1(predictions)

        confusion_matrix = self._compute_confusion_matrix(predictions)
        per_class_metrics = self._compute_per_class_metrics(predictions)

        roc_auc = None
        if compute_roc_auc and probabilities is not None and self.n_classes == 2:
            roc_auc = self._compute_roc_auc(probabilities)

        pr_auc = None
        if compute_pr_auc and probabilities is not None and self.n_classes == 2:
            pr_auc = self._compute_pr_auc(probabilities)

        avg_latency, throughput = None, None
        if benchmark_latency:
            avg_latency, throughput = self._benchmark_latency()

        metrics = EvaluationMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            roc_auc=roc_auc,
            pr_auc=pr_auc,
            confusion_matrix=confusion_matrix,
            per_class_metrics=per_class_metrics,
            avg_inference_time_ms=avg_latency,
            throughput_samples_per_sec=throughput,
        )

        logger.info("Evaluation complete: accuracy=%.4f, f1=%.4f", accuracy, f1)
        return metrics

    def _get_predictions(self) -> tuple[np.ndarray, np.ndarray | None]:
        """Get model predictions."""
        try:
            import torch

            if hasattr(self.model, "eval"):
                self.model.eval()

                with torch.no_grad():
                    inputs = torch.FloatTensor(self.test_features)

                    if hasattr(self.model, "to"):
                        device = next(self.model.parameters()).device
                        inputs = inputs.to(device)

                    outputs = self.model(inputs)

                    if isinstance(outputs, tuple):
                        outputs = outputs[0]

                    if outputs.dim() == 1:
                        probabilities = torch.sigmoid(outputs).cpu().numpy()
                        predictions = (probabilities > 0.5).astype(int)
                    else:
                        probabilities = torch.softmax(outputs, dim=1).cpu().numpy()
                        predictions = probabilities.argmax(axis=1)

                    return predictions, probabilities

        except ImportError:
            pass

        if hasattr(self.model, "predict"):
            predictions = self.model.predict(self.test_features)
            probabilities = None
            if hasattr(self.model, "predict_proba"):
                probabilities = self.model.predict_proba(self.test_features)
            return predictions, probabilities

        raise ValueError("Model does not have predict() or forward() method")

    def _compute_accuracy(self, predictions: np.ndarray) -> float:
        """Compute accuracy."""
        correct = (predictions == self.test_labels).sum()
        return float(correct / len(predictions))

    def _compute_precision(self, predictions: np.ndarray) -> float:
        """Compute precision (macro-averaged)."""
        precisions = []
        for class_id in np.unique(self.test_labels):
            tp = ((predictions == class_id) & (self.test_labels == class_id)).sum()
            fp = ((predictions == class_id) & (self.test_labels != class_id)).sum()
            if tp + fp > 0:
                precisions.append(tp / (tp + fp))
        return float(np.mean(precisions)) if precisions else 0.0

    def _compute_recall(self, predictions: np.ndarray) -> float:
        """Compute recall (macro-averaged)."""
        recalls = []
        for class_id in np.unique(self.test_labels):
            tp = ((predictions == class_id) & (self.test_labels == class_id)).sum()
            fn = ((predictions != class_id) & (self.test_labels == class_id)).sum()
            if tp + fn > 0:
                recalls.append(tp / (tp + fn))
        return float(np.mean(recalls)) if recalls else 0.0

    def _compute_f1(self, predictions: np.ndarray) -> float:
        """Compute F1 score (macro-averaged)."""
        precision = self._compute_precision(predictions)
        recall = self._compute_recall(predictions)
        if precision + recall > 0:
            return float(2 * precision * recall / (precision + recall))
        return 0.0

    def _compute_confusion_matrix(self, predictions: np.ndarray) -> np.ndarray:
        """Compute confusion matrix."""
        cm = np.zeros((self.n_classes, self.n_classes), dtype=int)
        for true_label, pred_label in zip(self.test_labels, predictions, strict=False):
            cm[true_label, pred_label] += 1
        return cm

    def _compute_per_class_metrics(self, predictions: np.ndarray) -> dict[int, dict[str, float]]:
        """Compute per-class metrics."""
        per_class = {}
        for class_id in np.unique(self.test_labels):
            tp = ((predictions == class_id) & (self.test_labels == class_id)).sum()
            fp = ((predictions == class_id) & (self.test_labels != class_id)).sum()
            fn = ((predictions != class_id) & (self.test_labels == class_id)).sum()

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

            per_class[int(class_id)] = {
                "precision": float(precision),
                "recall": float(recall),
                "f1_score": float(f1),
                "support": int(tp + fn),
            }
        return per_class

    def _compute_roc_auc(self, probabilities: np.ndarray) -> float:
        """Compute ROC-AUC (binary classification only)."""
        try:
            from sklearn.metrics import roc_auc_score

            if len(probabilities.shape) == 1:
                scores = probabilities
            else:
                scores = probabilities[:, 1]
            auc = roc_auc_score(self.test_labels, scores)
            return float(auc)
        except ImportError:
            logger.warning("sklearn not available for ROC-AUC computation")
            return 0.0

    def _compute_pr_auc(self, probabilities: np.ndarray) -> float:
        """Compute PR-AUC (binary classification only)."""
        try:
            from sklearn.metrics import average_precision_score

            if len(probabilities.shape) == 1:
                scores = probabilities
            else:
                scores = probabilities[:, 1]
            auc = average_precision_score(self.test_labels, scores)
            return float(auc)
        except ImportError:
            logger.warning("sklearn not available for PR-AUC computation")
            return 0.0

    def _benchmark_latency(self, n_iterations: int = 100) -> tuple[float, float]:
        """Benchmark inference latency."""
        import time

        latencies = []
        _ = self._get_predictions()

        for _ in range(n_iterations):
            start = time.time()
            _ = self._get_predictions()
            end = time.time()
            latency_ms = (end - start) * 1000
            latencies.append(latency_ms)

        avg_latency = np.mean(latencies)
        throughput = (self.n_samples / avg_latency) * 1000
        return float(avg_latency), float(throughput)

    def print_report(self, metrics: EvaluationMetrics) -> None:
        """Print evaluation report."""
        logger.info("=" * 80)
        logger.info("MODEL EVALUATION REPORT")
        logger.info("=" * 80)
        logger.info("\nOverall Metrics:")
        logger.info("  Accuracy:  %.4f", metrics.accuracy)
        logger.info("  Precision: %.4f", metrics.precision)
        logger.info("  Recall:    %.4f", metrics.recall)
        logger.info("  F1 Score:  %.4f", metrics.f1_score)

        if metrics.roc_auc:
            logger.info("  ROC-AUC:   %.4f", metrics.roc_auc)
        if metrics.pr_auc:
            logger.info("  PR-AUC:    %.4f", metrics.pr_auc)

        if metrics.per_class_metrics:
            logger.info("\nPer-Class Metrics:")
            for class_id, class_metrics in metrics.per_class_metrics.items():
                class_name = self.class_names[class_id] if self.class_names else f"Class {class_id}"
                logger.info("  %s:", class_name)
                logger.info("    Precision: %.4f", class_metrics["precision"])
                logger.info("    Recall:    %.4f", class_metrics["recall"])
                logger.info("    F1 Score:  %.4f", class_metrics["f1_score"])
                logger.info("    Support:   %s", class_metrics["support"])

        if metrics.avg_inference_time_ms:
            logger.info("\nPerformance:")
            logger.info("  Avg Inference Time: %.2f ms", metrics.avg_inference_time_ms)
            logger.info("  Throughput:         %.0f samples/sec", metrics.throughput_samples_per_sec)

        logger.info("=" * 80)

    def save_report(self, metrics: EvaluationMetrics, output_path: Path) -> None:
        """Save evaluation report to JSON."""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "n_samples": self.n_samples,
            "n_classes": self.n_classes,
            "metrics": metrics.to_dict(),
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info("Evaluation report saved to %s", output_path)
