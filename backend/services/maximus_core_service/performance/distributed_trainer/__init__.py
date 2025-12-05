"""Distributed Training Package."""

from __future__ import annotations

from .core import DistributedTrainer
from .models import DistributedConfig

__all__ = ["DistributedTrainer", "DistributedConfig"]
