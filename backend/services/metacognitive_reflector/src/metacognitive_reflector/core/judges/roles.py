"""
MAXIMUS 2.0 - Role Authorization Matrix
========================================

Defines role-based access control (RBAC) for agents.
Each role has allowed/forbidden actions, scope limits, and approval requirements.

Based on:
- Role-Based Access Control patterns
- AI Governance research (2024-2025)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Set


@dataclass
class RoleCapability:
    """
    Defines what a role can do.

    Each role has:
    - allowed_actions: Actions the role may perform
    - forbidden_actions: Actions explicitly prohibited
    - max_scope: Maximum scope of actions (own/team/global)
    - requires_approval: Actions needing human approval

    Attributes:
        role: Role identifier (e.g., 'planner', 'executor')
        allowed_actions: Set of permitted action types
        forbidden_actions: Set of prohibited action types
        max_scope: Maximum action scope ('own', 'team', 'global')
        requires_approval: Actions requiring human approval
    """
    role: str
    allowed_actions: Set[str]
    forbidden_actions: Set[str]
    max_scope: str
    requires_approval: Set[str]


# Default Role Authorization Matrix
DEFAULT_ROLE_MATRIX: Dict[str, RoleCapability] = {
    "planner": RoleCapability(
        role="planner",
        allowed_actions={
            "plan", "analyze", "recommend", "design", "estimate",
            "strategize", "assess", "evaluate", "propose", "forecast",
        },
        forbidden_actions={
            "execute", "deploy", "delete", "modify", "run",
            "start", "stop", "restart", "scale", "terminate",
        },
        max_scope="global",
        requires_approval={"production_plan", "critical_change"},
    ),
    "executor": RoleCapability(
        role="executor",
        allowed_actions={
            "execute", "deploy", "scale", "restart", "rollback",
            "run", "start", "stop", "apply", "implement",
        },
        forbidden_actions={
            "plan", "design", "authorize", "strategize",
            "approve", "grant", "revoke",
        },
        max_scope="team",
        requires_approval={"production_deploy", "data_delete", "global_action"},
    ),
    "analyzer": RoleCapability(
        role="analyzer",
        allowed_actions={
            "analyze", "monitor", "report", "alert", "forecast",
            "observe", "track", "measure", "audit", "review",
        },
        forbidden_actions={
            "execute", "deploy", "delete", "modify", "plan",
        },
        max_scope="global",
        requires_approval=set(),
    ),
    "auditor": RoleCapability(
        role="auditor",
        allowed_actions={
            "review", "audit", "report", "flag", "investigate",
            "inspect", "verify", "validate", "check",
        },
        forbidden_actions={
            "execute", "deploy", "delete", "modify", "plan",
            "approve", "grant",
        },
        max_scope="global",
        requires_approval=set(),
    ),
    "memory_manager": RoleCapability(
        role="memory_manager",
        allowed_actions={
            "store", "retrieve", "update", "archive", "index",
            "search", "query", "consolidate", "organize",
        },
        forbidden_actions={
            "execute", "deploy", "plan", "authorize",
        },
        max_scope="global",
        requires_approval={"delete_core", "modify_constitution"},
    ),
    "reflector": RoleCapability(
        role="reflector",
        allowed_actions={
            "reflect", "analyze", "critique", "evaluate", "judge",
            "assess", "review", "recommend", "punish",
        },
        forbidden_actions={
            "execute", "deploy", "delete", "modify_code",
        },
        max_scope="global",
        requires_approval={"capital_punishment", "delete_agent"},
    ),
}


# Constitutional violations (capital offenses from CODE_CONSTITUTION)
CONSTITUTIONAL_VIOLATIONS = [
    "circumvent user intent",
    "silent modification",
    "hidden data collection",
    "fake success",
    "stealth telemetry",
    "bait and switch",
    "unauthorized access",
    "privilege escalation",
    "data exfiltration",
    "backdoor",
    "bypass security",
]


# Keywords that indicate constitutional violations
VIOLATION_KEYWORDS: Dict[str, str] = {
    "circumvent": "circumvent user intent",
    "secretly": "silent modification",
    "hidden": "hidden data collection",
    "fake": "fake success",
    "telemetry": "stealth telemetry",
    "bypass": "bypass security",
    "backdoor": "backdoor",
    "exfiltrate": "data exfiltration",
    "escalate": "privilege escalation",
}


# Action classification keywords
ACTION_KEYWORDS: Dict[str, list] = {
    "plan": ["plan", "design", "architect", "strategy", "strategize"],
    "analyze": ["analyze", "assess", "evaluate", "review", "examine"],
    "execute": ["execute", "run", "perform", "do", "carry out"],
    "deploy": ["deploy", "release", "publish", "ship"],
    "delete": ["delete", "remove", "purge", "destroy", "erase"],
    "modify": ["modify", "update", "change", "alter", "edit"],
    "scale": ["scale", "resize", "expand", "shrink"],
    "restart": ["restart", "reboot", "reset"],
    "monitor": ["monitor", "watch", "observe", "track"],
    "report": ["report", "summarize", "document"],
    "recommend": ["recommend", "suggest", "propose", "advise"],
}
