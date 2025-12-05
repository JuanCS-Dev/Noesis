"""
HITL Risk Assessor Package.

Comprehensive risk assessment engine for security decisions.

This package provides:
- Multi-dimensional risk analysis (16 factors)
- Category-level risk scoring (6 categories)
- Risk level classification (CRITICAL/HIGH/MEDIUM/LOW)
- Justifications and mitigation recommendations

Risk Dimensions:
- Threat Severity: How dangerous is the threat?
- Asset Criticality: How important are affected assets?
- Business Impact: What's the business consequence?
- Action Reversibility: Can the action be undone?
- Blast Radius: How many assets/users affected?
- Compliance Impact: Regulatory implications?

Risk Score: 0.0 (no risk) to 1.0 (maximum risk)
Risk Level: LOW, MEDIUM, HIGH, CRITICAL

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Refactored: 2025-12-03
"""

from __future__ import annotations

# Core risk assessor
from .core import RiskAssessor

# Data models
from .models import RiskFactors, RiskScore

# Constants
from .constants import (
    ACTION_AGGRESSIVENESS,
    ACTION_REVERSIBILITY,
    CRITICAL_THRESHOLD,
    CRITICALITY_SCORES,
    HIGH_THRESHOLD,
    MEDIUM_THRESHOLD,
    OPERATIONAL_IMPACT_KEYWORDS,
    RISK_WEIGHTS,
    SCOPE_SCORES,
    SENSITIVITY_SCORES,
)

# Mixins (for advanced usage)
from .classification import ClassificationMixin
from .factors import FactorComputationMixin
from .recommendations import RecommendationsMixin
from .scoring import ScoringMixin

__all__ = [
    # Main classes
    "RiskAssessor",
    "RiskFactors",
    "RiskScore",
    # Constants
    "RISK_WEIGHTS",
    "ACTION_AGGRESSIVENESS",
    "ACTION_REVERSIBILITY",
    "CRITICAL_THRESHOLD",
    "HIGH_THRESHOLD",
    "MEDIUM_THRESHOLD",
    "CRITICALITY_SCORES",
    "SENSITIVITY_SCORES",
    "OPERATIONAL_IMPACT_KEYWORDS",
    "SCOPE_SCORES",
    # Mixins
    "FactorComputationMixin",
    "ScoringMixin",
    "ClassificationMixin",
    "RecommendationsMixin",
]
