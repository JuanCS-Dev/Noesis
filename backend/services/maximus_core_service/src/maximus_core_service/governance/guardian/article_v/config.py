"""Article V Guardian Configuration.

Configuration constants and defaults for Article V Guardian.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-13
"""

from __future__ import annotations

# Default paths for monitoring
DEFAULT_AUTONOMOUS_PATHS = [
    "/home/juan/vertice-dev/backend/services/maximus_core_service",
    "/home/juan/vertice-dev/backend/services/reactive_fabric_core",
    "/home/juan/vertice-dev/backend/services/active_immune_core",
]

DEFAULT_POWERFUL_PATHS = [
    "/home/juan/vertice-dev/backend/services/maximus_core_service",
    "/home/juan/vertice-dev/backend/security/offensive",
]

DEFAULT_HITL_PATHS = [
    "/home/juan/vertice-dev/backend/services/maximus_core_service",
    "/home/juan/vertice-dev/backend/services/reactive_fabric_core",
]

DEFAULT_PROCESS_PATHS = [
    "/home/juan/vertice-dev/backend/services/maximus_core_service",
    "/home/juan/vertice-dev/backend/services/reactive_fabric_core",
    "/home/juan/vertice-dev/backend/services/active_immune_core",
]

DEFAULT_GOVERNANCE_PATHS = [
    "/home/juan/vertice-dev/backend/services/maximus_core_service/governance",
    "/home/juan/vertice-dev/backend/services/maximus_core_service/api",
]

# Responsibility Doctrine requirements
RESPONSIBILITY_REQUIREMENTS = [
    "compartmentalization",  # Need-to-know
    "two_man_rule",  # Critical actions need dual approval
    "kill_switch",  # Emergency stop capability
    "audit_trail",  # Complete logging
    "hitl_control",  # Human-in-the-loop for critical ops
]

# Autonomous capability indicators
AUTONOMOUS_INDICATORS = [
    "autonomous",
    "auto_execute",
    "self_",
    "ai_agent",
    "automatic",
    "unattended",
    "scheduled_task",
    "background_worker",
]

# Governance indicators
GOVERNANCE_INDICATORS = [
    "policy",
    "governance",
    "approval",
    "authorization",
    "oversight",
    "review",
    "audit",
    "control",
]

# Critical patterns requiring HITL
CRITICAL_HITL_PATTERNS = [
    r"production.*deploy",
    r"database.*drop",
    r"delete.*user",
    r"financial.*transaction",
    r"security.*override",
    r"admin.*privilege",
    r"system.*shutdown",
]

# HITL indicators
HITL_INDICATORS = [
    "human_approval",
    "require_confirmation",
    "manual_review",
    "operator_decision",
    "hitl",
    "human_in_the_loop",
    "await_approval",
]

# Process patterns for kill switch check
PROCESS_PATTERNS = [
    r"while True:",
    r"asyncio\.run",
    r"thread",
    r"daemon",
    r"worker",
    r"scheduler",
    r"loop\.run_forever",
]

# Kill switch indicators
KILLSWITCH_PATTERNS = [
    "kill_switch",
    "emergency_stop",
    "shutdown",
    "terminate",
    "stop_signal",
    "abort",
    "circuit_breaker",
]

# Critical actions requiring dual approval
CRITICAL_ACTIONS = [
    "deploy.*production",
    "delete.*database",
    "financial.*transfer",
    "security.*bypass",
    "admin.*grant",
    "config.*override",
]

# Two-Man Rule indicators
TWOMAN_PATTERNS = [
    "dual_approval",
    "two_man",
    "require_second",
    "double_confirmation",
    "multi_signature",
    "cosign",
]

# Powerful operations
POWERFUL_OPERATIONS = [
    "exploit",
    "attack",
    "delete",
    "destroy",
    "wipe",
    "execute_command",
    "shell",
    "subprocess",
]
