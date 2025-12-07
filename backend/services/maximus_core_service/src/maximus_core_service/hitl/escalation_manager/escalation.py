"""
Escalation Execution Mixin.

Handles escalation of decisions to higher authority.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from ..base_pkg import DecisionStatus
from .enums import EscalationType
from .models import EscalationEvent, EscalationRule

if TYPE_CHECKING:
    from ..base_pkg import HITLDecision, RiskLevel


class EscalationExecutionMixin:
    """
    Mixin for escalation execution.

    Handles escalating decisions and determining escalation targets.
    """

    # Default escalation chain
    DEFAULT_CHAIN = [
        "soc_operator",
        "soc_supervisor",
        "security_manager",
        "ciso",
        "ceo",
    ]

    def escalate_decision(
        self,
        decision: HITLDecision,
        escalation_type: EscalationType,
        reason: str,
        target_role: str | None = None,
        triggered_rule: EscalationRule | None = None,
    ) -> EscalationEvent:
        """
        Escalate decision to higher authority.

        Args:
            decision: Decision to escalate
            escalation_type: Type of escalation
            reason: Escalation reason
            target_role: Target role (auto-determined if not provided)
            triggered_rule: Rule that triggered escalation

        Returns:
            EscalationEvent record
        """
        # Determine target role
        if target_role is None:
            if triggered_rule:
                target_role = triggered_rule.target_role
            else:
                target_role = self.config.get_escalation_target(decision.risk_level)

        # Get current role
        from_role = decision.assigned_operator or "unassigned"

        # Create escalation event
        event = EscalationEvent(
            event_id=f"esc_{datetime.utcnow().timestamp()}",
            decision_id=decision.decision_id,
            escalation_type=escalation_type,
            from_role=from_role,
            to_role=target_role,
            reason=reason,
            rule_id=triggered_rule.rule_id if triggered_rule else None,
        )

        # Update decision
        decision.status = DecisionStatus.ESCALATED
        decision.escalated = True
        decision.escalated_to = target_role
        decision.escalated_at = datetime.utcnow()
        decision.escalation_reason = reason

        # Send notifications
        if triggered_rule:
            self._send_notifications(decision, event, triggered_rule)
        else:
            self._send_notifications(decision, event)

        # Record event
        self.escalation_history.append(event)

        # Update metrics
        self.metrics["total_escalations"] += 1
        metric_key = f"{escalation_type.value}_escalations"
        if metric_key in self.metrics:
            self.metrics[metric_key] += 1

        self.logger.info(
            "Decision escalated: %s → %s (type=%s, reason=%s)",
            decision.decision_id,
            target_role,
            escalation_type.value,
            reason,
        )

        return event

    def get_escalation_target(self, current_role: str, decision: HITLDecision) -> str:
        """
        Get next escalation target in chain.

        Args:
            current_role: Current assigned role
            decision: Decision to escalate

        Returns:
            Next role in escalation chain
        """
        from ..base_pkg import RiskLevel

        # Use risk-based target if critical/high risk
        if decision.risk_level == RiskLevel.CRITICAL:
            return self.config.critical_risk_escalation
        if decision.risk_level == RiskLevel.HIGH:
            return self.config.high_risk_escalation

        # Otherwise, use escalation chain
        chain = self.config.sla_config.escalation_chain or self.DEFAULT_CHAIN

        try:
            current_index = chain.index(current_role)
            if current_index < len(chain) - 1:
                return chain[current_index + 1]
            # Already at top of chain
            return chain[-1]
        except ValueError:
            # Current role not in chain, use default
            return self.config.get_escalation_target(decision.risk_level)
