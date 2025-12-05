"""SHAP Configuration.

Configuration settings for SHAP explainer.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SHAPConfig:
    """Configuration for SHAP explainer.

    Attributes:
        algorithm: SHAP algorithm ('kernel', 'tree', 'deep', 'linear').
        num_background_samples: Number of background samples for kernel SHAP.
        num_features: Number of top features to compute (None = all).
        check_additivity: Whether to check that SHAP values sum to prediction.
    """

    algorithm: str = "kernel"
    num_background_samples: int = 100
    num_features: int | None = None
    check_additivity: bool = False
