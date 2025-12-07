"""Bias Mitigation Engine for Cybersecurity AI Models.

This module implements bias mitigation strategies to reduce unfair treatment
across protected groups while maintaining model performance.

Mitigation Strategies:
    - Pre-processing: Reweighing training data
    - In-processing: Regularization-based debiasing
    - Post-processing: Threshold optimization
    - Calibration adjustment
"""

from __future__ import annotations

from .engine import MitigationEngine

__all__ = ["MitigationEngine"]
