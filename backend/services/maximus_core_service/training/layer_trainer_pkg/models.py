"""Models for training module."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TrainingConfig:
    """Training configuration."""
    
    epochs: int = 10
    batch_size: int = 32
    learning_rate: float = 0.001
