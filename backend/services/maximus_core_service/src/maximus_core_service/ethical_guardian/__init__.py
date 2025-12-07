"""
Ethical Guardian Package.

Integração completa do Ethical AI Stack no MAXIMUS.
Valida ações através de 7 fases éticas.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from __future__ import annotations

from .guardian import EthicalGuardian
from .models import (
    ComplianceCheckResult,
    EthicalDecisionResult,
    EthicalDecisionType,
    EthicsCheckResult,
    FairnessCheckResult,
    FLCheckResult,
    GovernanceCheckResult,
    HITLCheckResult,
    PrivacyCheckResult,
    XAICheckResult,
)

__all__ = [
    # Main class
    "EthicalGuardian",
    # Enum
    "EthicalDecisionType",
    # Result models
    "EthicalDecisionResult",
    "GovernanceCheckResult",
    "EthicsCheckResult",
    "XAICheckResult",
    "ComplianceCheckResult",
    "FairnessCheckResult",
    "PrivacyCheckResult",
    "FLCheckResult",
    "HITLCheckResult",
]
