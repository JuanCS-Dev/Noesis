"""Shim for backward compatibility."""
from .layer_trainer_legacy import LayerTrainer, TrainingConfig, TrainingMetrics, EarlyStopping

__all__ = ["LayerTrainer", "TrainingConfig", "TrainingMetrics", "EarlyStopping"]
