"""
Escalation Data Models.

Contains escalation rules and events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from .enums import EscalationType

if TYPE_CHECKING:
    from ..base_pkg import HITLDecision, RiskLevel


@dataclass
class EscalationRule:
    """
    Rule for when to escalate a decision.
    """

    # Rule identifier
    rule_id: str
    rule_name: str
    escalation_type: EscalationType

    # Trigger conditions
    risk_levels: list[RiskLevel] = field(default_factory=list)  # Empty = all levels
    max_rejections: int = 2
    timeout_threshold: timedelta | None = None

    # Escalation target
    target_role: str = "soc_supervisor"

    # Notification settings
    send_email: bool = True
    send_sms: bool = False
    send_slack: bool = True

    # Rule priority (higher = more important)
    priority: int = 0

    # Active flag
    active: bool = True

    def matches(self, decision: HITLDecision) -> bool:
        """
        Check if rule matches decision.

        Args:
            decision: Decision to check

        Returns:
            True if rule matches
        """
        from ..base_pkg import RiskLevel

        if not self.active:
            return False

        # Check risk level filter
        if self.risk_levels and decision.risk_level not in self.risk_levels:
            return False

        # Type-specific checks
        if self.escalation_type == EscalationType.TIMEOUT:
            return decision.is_overdue()

        if self.escalation_type == EscalationType.HIGH_RISK:
            return decision.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

        if self.escalation_type == EscalationType.MULTIPLE_REJECTIONS:
            rejection_count = decision.metadata.get("rejection_count", 0)
            return rejection_count >= self.max_rejections

        if self.escalation_type == EscalationType.STALE_DECISION:
            if self.timeout_threshold:
                age = decision.get_age()
                return age > self.timeout_threshold
            return False

        return False


@dataclass
class EscalationEvent:
    """
    Record of an escalation event.
    """

    # Event details
    event_id: str
    decision_id: str
    escalation_type: EscalationType
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Escalation details
    from_role: str = ""
    to_role: str = ""
    reason: str = ""

    # Triggered rule
    rule_id: str | None = None

    # Notification status
    email_sent: bool = False
    sms_sent: bool = False
    slack_sent: bool = False

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
