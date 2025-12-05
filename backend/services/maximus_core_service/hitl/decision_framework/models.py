"""
Decision Framework Data Models.

Contains decision result and related data structures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..base_pkg import HITLDecision


@dataclass
class DecisionResult:
    """
    Result of decision processing.

    Indicates whether decision was executed immediately, queued for review,
    or rejected.
    """

    # Decision reference
    decision: HITLDecision

    # Result status
    executed: bool = False
    queued: bool = False
    rejected: bool = False

    # Execution details
    execution_output: dict[str, Any] = field(default_factory=dict)
    execution_error: str | None = None

    # Audit trail entry
    audit_entry_id: str | None = None

    # Timing
    processing_time: float = 0.0  # seconds

    def get_summary(self) -> str:
        """Get human-readable summary."""
        if self.executed:
            return f"Executed: {self.decision.context.action_type.value} (ID: {self.decision.decision_id})"
        if self.queued:
            return f"Queued for review: {self.decision.context.action_type.value} (ID: {self.decision.decision_id})"
        if self.rejected:
            return f"Rejected: {self.decision.context.action_type.value} (ID: {self.decision.decision_id})"
        return f"Pending: {self.decision.decision_id}"
