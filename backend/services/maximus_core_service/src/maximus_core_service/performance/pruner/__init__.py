"""
Model Pruning Package.

Prune neural networks for faster inference and smaller models.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Refactored: 2025-12-03
"""

from __future__ import annotations

from .core import ModelPruner
from .models import PruningConfig, PruningResult

__all__ = [
    "ModelPruner",
    "PruningConfig",
    "PruningResult",
]
