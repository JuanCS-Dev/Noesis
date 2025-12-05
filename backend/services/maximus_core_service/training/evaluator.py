"""Shim for training.evaluator."""
from .evaluator_pkg import ModelEvaluator, EvaluationMetrics

# Alias for backward compatibility if needed
Evaluator = ModelEvaluator

__all__ = ["ModelEvaluator", "EvaluationMetrics", "Evaluator"]
