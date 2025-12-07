"""
Governance Module - Ethical Governance Framework.

Core data structures for the VÉRTICE Platform's ethical governance framework,
including Ethics Review Board (ERB), policy management, and audit infrastructure.

This module provides the foundation for Phase 0: Foundation & Governance.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Refactored: 2025-12-03
"""

from __future__ import annotations

# Configuration
from .config import GovernanceConfig

# Enums
from .enums import (
    AuditLogLevel,
    DecisionType,
    ERBMemberRole,
    GovernanceAction,
    PolicySeverity,
    PolicyType,
)

# ERB models
from .erb import ERBDecision, ERBMeeting, ERBMember

# Policy models
from .policy import Policy, PolicyEnforcementResult, PolicyViolation

# Audit models
from .audit import AuditLog

# Whistleblower models
from .whistleblower import WhistleblowerReport

# Results
from .results import GovernanceResult

__all__ = [
    # Configuration
    "GovernanceConfig",
    # Enums
    "PolicyType",
    "PolicySeverity",
    "ERBMemberRole",
    "DecisionType",
    "AuditLogLevel",
    "GovernanceAction",
    # ERB
    "ERBMember",
    "ERBMeeting",
    "ERBDecision",
    # Policy
    "Policy",
    "PolicyViolation",
    "PolicyEnforcementResult",
    # Audit
    "AuditLog",
    # Whistleblower
    "WhistleblowerReport",
    # Results
    "GovernanceResult",
]
