"""Batch Prediction Models and Configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BatchPredictorConfig:
    """Batch predictor configuration."""

    batch_size: int = 32
    num_workers: int = 4
    device: str = "cuda"
    fp16: bool = False
    max_batches: int | None = None


@dataclass
class BatchPredictionResult:
    """Batch prediction result."""

    predictions: list[Any] = field(default_factory=list)
    num_samples: int = 0
    total_time: float = 0.0
    avg_time_per_sample: float = 0.0
    throughput: float = 0.0
