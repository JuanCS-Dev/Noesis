"""
Audit and Statistics Module.

Handles decision logging and statistics tracking.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from governance import AuditLogger, GovernanceAction

from .models import EthicalDecisionResult

if TYPE_CHECKING:
    pass


async def log_decision(
    audit_logger: AuditLogger | None,
    decision: EthicalDecisionResult,
) -> str | None:
    """
    Log decision to audit trail.

    Args:
        audit_logger: AuditLogger instance (or None if disabled)
        decision: Decision result to log

    Returns:
        Log ID if successful, None otherwise
    """
    if not audit_logger:
        return None

    try:
        log_id = audit_logger.log(
            action=GovernanceAction.ERB_DECISION_MADE,
            actor=decision.actor,
            description=(
                f"Ethical decision for action '{decision.action}': "
                f"{decision.decision_type.value}"
            ),
            target_entity_type="action",
            target_entity_id=decision.action,
            details=decision.to_dict(),
        )
        decision.audit_log_id = log_id
        return log_id
    except Exception:
        return None


def get_statistics(
    total_validations: int,
    total_approved: int,
    total_rejected: int,
    avg_duration_ms: float,
    enable_governance: bool,
    enable_ethics: bool,
    enable_xai: bool,
    enable_compliance: bool,
) -> dict[str, Any]:
    """
    Get validation statistics.

    Args:
        total_validations: Total number of validations performed
        total_approved: Number of approved actions
        total_rejected: Number of rejected actions
        avg_duration_ms: Average duration in milliseconds
        enable_governance: Whether governance is enabled
        enable_ethics: Whether ethics is enabled
        enable_xai: Whether XAI is enabled
        enable_compliance: Whether compliance is enabled

    Returns:
        Dictionary with statistics
    """
    return {
        "total_validations": total_validations,
        "total_approved": total_approved,
        "total_rejected": total_rejected,
        "approval_rate": (
            total_approved / total_validations if total_validations > 0 else 0.0
        ),
        "avg_duration_ms": avg_duration_ms,
        "enabled_phases": {
            "governance": enable_governance,
            "ethics": enable_ethics,
            "xai": enable_xai,
            "compliance": enable_compliance,
        },
    }
