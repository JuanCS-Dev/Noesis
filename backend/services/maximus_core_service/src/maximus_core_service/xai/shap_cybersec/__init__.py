"""CyberSecSHAP - SHAP adapted for cybersecurity deep learning models.

This module implements SHAP (SHapley Additive exPlanations) specifically adapted
for cybersecurity use cases, supporting neural networks, tree-based models, and
deep learning models used in threat detection.

Key Adaptations:
    - Kernel SHAP for model-agnostic explanations
    - Tree SHAP for XGBoost/LightGBM models
    - Deep SHAP for neural networks
    - Cybersecurity-specific background datasets
    - Optimized for real-time explanation generation
"""

from __future__ import annotations

from .config import SHAPConfig
from .explainer import CyberSecSHAP

__all__ = [
    "SHAPConfig",
    "CyberSecSHAP",
]
