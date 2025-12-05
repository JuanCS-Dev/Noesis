"""Counterfactual configuration.

Configuration dataclass for counterfactual generation.

Author: Juan Carlos de Souza
Date: 2025-10-06
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CounterfactualConfig:
    """Configuration for counterfactual generation.

    Attributes:
        desired_outcome: Desired prediction outcome
        max_iterations: Maximum optimization iterations
        num_candidates: Number of candidates to generate
        proximity_weight: Weight for proximity objective
        sparsity_weight: Weight for sparsity objective (prefer fewer changes)
        validity_weight: Weight for validity objective (valid cybersec values)
    """

    desired_outcome: Any | None = None
    max_iterations: int = 1000
    num_candidates: int = 10
    proximity_weight: float = 1.0
    sparsity_weight: float = 0.5
    validity_weight: float = 0.3
