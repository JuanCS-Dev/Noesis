"""
Phase 0: Governance Check.

Target: <20ms

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from governance import PolicyEngine, PolicyType

from .models import GovernanceCheckResult

if TYPE_CHECKING:
    pass


async def governance_check(
    policy_engine: PolicyEngine,
    action: str,
    context: dict[str, Any],
    actor: str,
) -> GovernanceCheckResult:
    """
    Phase 0: Check governance policies.

    Target: <20ms

    Args:
        policy_engine: PolicyEngine instance
        action: Action being validated
        context: Action context
        actor: Actor performing action

    Returns:
        GovernanceCheckResult with compliance status
    """
    start_time = time.time()

    # Determine which policies to check
    policies_to_check = [PolicyType.ETHICAL_USE]

    # Red teaming if offensive action
    if any(
        keyword in action.lower()
        for keyword in [
            "exploit",
            "attack",
            "scan",
            "pentest",
            "brute",
            "inject",
        ]
    ):
        policies_to_check.append(PolicyType.RED_TEAMING)

    # Data privacy if processes personal data
    if context.get("processes_personal_data") or context.get("has_pii"):
        policies_to_check.append(PolicyType.DATA_PRIVACY)

    # Check each policy
    violations = []
    warnings = []

    for policy_type in policies_to_check:
        policy_result = policy_engine.enforce_policy(
            policy_type=policy_type, action=action, context=context, actor=actor
        )

        if not policy_result.is_compliant:
            for violation in policy_result.violations:
                violations.append(
                    {
                        "policy": policy_type.value,
                        "title": violation.title,
                        "severity": violation.severity.value,
                        "rule": violation.violated_rule,
                    }
                )

        if policy_result.warnings:
            warnings.extend(policy_result.warnings)

    duration_ms = (time.time() - start_time) * 1000

    return GovernanceCheckResult(
        is_compliant=len(violations) == 0,
        policies_checked=policies_to_check,
        violations=violations,
        warnings=warnings,
        duration_ms=duration_ms,
    )
