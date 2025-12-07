"""Feature constraints for counterfactual generation.

Cybersecurity-specific feature constraints and validation.

Author: Juan Carlos de Souza
Date: 2025-10-06
"""

from __future__ import annotations

from typing import Any

import numpy as np


def init_feature_constraints() -> dict[str, dict[str, Any]]:
    """Initialize cybersecurity-specific feature constraints.

    Returns:
        Dictionary of feature constraints
    """
    return {
        "port": {"min": 1, "max": 65535, "type": "int"},
        "src_port": {"min": 1, "max": 65535, "type": "int"},
        "dst_port": {"min": 1, "max": 65535, "type": "int"},
        "score": {"min": 0.0, "max": 1.0, "type": "float"},
        "threat_score": {"min": 0.0, "max": 1.0, "type": "float"},
        "anomaly_score": {"min": 0.0, "max": 1.0, "type": "float"},
        "confidence": {"min": 0.0, "max": 1.0, "type": "float"},
        "severity": {"min": 0.0, "max": 1.0, "type": "float"},
        "probability": {"min": 0.0, "max": 1.0, "type": "float"},
        "packet_size": {"min": 0, "max": 65535, "type": "int"},
        "payload_size": {"min": 0, "max": 65535, "type": "int"},
    }


def apply_constraints(
    feature_name: str,
    value: float,
    feature_constraints: dict[str, dict[str, Any]],
) -> float:
    """Apply constraints to feature value.

    Args:
        feature_name: Feature name
        value: Value to constrain
        feature_constraints: Dictionary of feature constraints

    Returns:
        Constrained value
    """
    for pattern, constraint in feature_constraints.items():
        if pattern in feature_name.lower():
            value = np.clip(value, constraint["min"], constraint["max"])

            if constraint["type"] == "int":
                value = round(value)

            return value

    return value
