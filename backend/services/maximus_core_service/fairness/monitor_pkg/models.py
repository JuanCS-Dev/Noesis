"""Fairness Monitor Models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FairnessMetrics:
    """Fairness metrics."""
    
    demographic_parity: float = 0.0
    equal_opportunity: float = 0.0
    disparate_impact: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
