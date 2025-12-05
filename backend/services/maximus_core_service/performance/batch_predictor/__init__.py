"""
Batch Predictor Package.

Efficient batch prediction for inference.

Author: Claude Code + JuanCS-Dev  
Date: 2025-10-06
Refactored: 2025-12-03
"""

from __future__ import annotations

from .core import BatchPredictor
from .models import BatchPredictorConfig, BatchPredictionResult

__all__ = [
    "BatchPredictor",
    "BatchPredictorConfig",
    "BatchPredictionResult",
]
