"""
Decision Queue Data Models.

Contains queued decision wrapper.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..base_pkg import HITLDecision


@dataclass
class QueuedDecision:
    """
    Wrapper for decision in queue with queueing metadata.
    """

    # Decision reference
    decision: HITLDecision

    # Queue metadata
    queued_at: datetime = field(default_factory=datetime.utcnow)
    queue_position: int = 0
    priority_score: float = 0.0  # Higher = more urgent

    # Assignment tracking
    assigned: bool = False
    assignment_attempts: int = 0

    # SLA tracking
    sla_warning_sent: bool = False
    sla_violated: bool = False

    def get_time_in_queue(self) -> timedelta:
        """Get time decision has been in queue."""
        return datetime.utcnow() - self.queued_at

    def get_time_until_sla(self) -> timedelta | None:
        """Get time remaining until SLA deadline."""
        if self.decision.sla_deadline is None:
            return None
        remaining = self.decision.sla_deadline - datetime.utcnow()
        return remaining if remaining.total_seconds() > 0 else timedelta(0)

    def is_sla_violated(self) -> bool:
        """Check if SLA has been violated."""
        if self.decision.sla_deadline is None:
            return False
        return datetime.utcnow() > self.decision.sla_deadline

    def should_send_sla_warning(self, warning_threshold: float = 0.75) -> bool:
        """Check if SLA warning should be sent."""
        if self.sla_warning_sent or self.decision.sla_deadline is None:
            return False

        time_in_queue = self.get_time_in_queue()
        total_sla = self.decision.sla_deadline - self.decision.created_at

        if total_sla.total_seconds() <= 0:
            return False

        fraction_elapsed = time_in_queue.total_seconds() / total_sla.total_seconds()
        return fraction_elapsed >= warning_threshold
