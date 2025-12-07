"""Counterfactual Explanation Generator for cybersecurity models.

This package generates counterfactual explanations ("what-if" scenarios) for
cybersecurity predictions, helping users understand what changes would result
in different decisions.

Key Features:
    - Minimal perturbation counterfactuals (closest alternative)
    - Actionable recommendations for security operators
    - Cybersecurity-specific constraints (valid IPs, ports, scores)
    - Multi-objective optimization (proximity + sparsity + validity)

Author: Juan Carlos de Souza
Date: 2025-10-06
"""

from __future__ import annotations

from .config import CounterfactualConfig
from .constraints import apply_constraints, init_feature_constraints
from .formatting import (
    calculate_counterfactual_confidence,
    create_no_counterfactual_result,
    generate_counterfactual_summary,
    generate_visualization_data,
)
from .generator import CounterfactualGenerator
from .perturbation import (
    compute_gradients,
    generate_counterfactual_candidates,
    generate_gradient_based_cf,
    generate_random_perturbation,
    perturb_feature,
)
from .selection import identify_changed_features, select_best_counterfactual
from .utils import (
    determine_desired_outcome,
    dict_to_array,
    get_prediction,
    matches_desired_outcome,
)

__all__ = [
    # Main class
    "CounterfactualGenerator",
    # Config
    "CounterfactualConfig",
    # Constraints
    "init_feature_constraints",
    "apply_constraints",
    # Utils
    "dict_to_array",
    "get_prediction",
    "matches_desired_outcome",
    "determine_desired_outcome",
    # Perturbation
    "perturb_feature",
    "generate_random_perturbation",
    "compute_gradients",
    "generate_gradient_based_cf",
    "generate_counterfactual_candidates",
    # Selection
    "select_best_counterfactual",
    "identify_changed_features",
    # Formatting
    "generate_counterfactual_summary",
    "calculate_counterfactual_confidence",
    "generate_visualization_data",
    "create_no_counterfactual_result",
]
