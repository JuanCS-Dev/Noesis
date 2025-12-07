"""Article V Guardian - Prior Legislation Enforcement.

Enforces Article V of the Vértice Constitution: The Principle of Prior Legislation.
Ensures governance systems are implemented BEFORE autonomous systems of power.

Key Enforcement Areas:
- Section 1: Governance must be designed/implemented before autonomous systems
- Section 2: Responsibility Doctrine must be applied to all autonomous AI workflows

Author: Claude Code + JuanCS-Dev
Date: 2025-10-13
"""

from __future__ import annotations

from .checkers import (
    check_autonomous_governance,
    check_hitl_controls,
    check_kill_switches,
    check_responsibility_doctrine,
    check_two_man_rule,
)
from .config import (
    AUTONOMOUS_INDICATORS,
    CRITICAL_ACTIONS,
    CRITICAL_HITL_PATTERNS,
    DEFAULT_AUTONOMOUS_PATHS,
    DEFAULT_GOVERNANCE_PATHS,
    DEFAULT_HITL_PATHS,
    DEFAULT_POWERFUL_PATHS,
    DEFAULT_PROCESS_PATHS,
    GOVERNANCE_INDICATORS,
    HITL_INDICATORS,
    KILLSWITCH_PATTERNS,
    POWERFUL_OPERATIONS,
    PROCESS_PATTERNS,
    RESPONSIBILITY_REQUIREMENTS,
    TWOMAN_PATTERNS,
)
from .guardian import ArticleVGuardian
from .registry import register_governance, validate_governance_precedence

__all__ = [
    # Main class
    "ArticleVGuardian",
    # Checkers
    "check_autonomous_governance",
    "check_responsibility_doctrine",
    "check_hitl_controls",
    "check_kill_switches",
    "check_two_man_rule",
    # Registry
    "register_governance",
    "validate_governance_precedence",
    # Config constants
    "RESPONSIBILITY_REQUIREMENTS",
    "AUTONOMOUS_INDICATORS",
    "GOVERNANCE_INDICATORS",
    "CRITICAL_HITL_PATTERNS",
    "HITL_INDICATORS",
    "PROCESS_PATTERNS",
    "KILLSWITCH_PATTERNS",
    "CRITICAL_ACTIONS",
    "TWOMAN_PATTERNS",
    "POWERFUL_OPERATIONS",
    "DEFAULT_AUTONOMOUS_PATHS",
    "DEFAULT_POWERFUL_PATHS",
    "DEFAULT_HITL_PATHS",
    "DEFAULT_PROCESS_PATHS",
    "DEFAULT_GOVERNANCE_PATHS",
]
