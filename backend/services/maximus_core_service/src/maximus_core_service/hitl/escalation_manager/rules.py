"""
Escalation Rules Mixin.

Handles rule initialization and checking.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .enums import EscalationType
from .models import EscalationRule

if TYPE_CHECKING:
    from ..base_pkg import HITLDecision, RiskLevel


class EscalationRulesMixin:
    """
    Mixin for escalation rule management.

    Handles rule initialization, addition, and matching.
    """

    def _initialize_default_rules(self) -> None:
        """Initialize default escalation rules."""
        from ..base_pkg import RiskLevel

        # Rule 1: Timeout escalation
        self.rules.append(
            EscalationRule(
                rule_id="timeout_escalation",
                rule_name="SLA Timeout Escalation",
                escalation_type=EscalationType.TIMEOUT,
                target_role=self.config.low_risk_escalation,
                send_email=True,
                send_slack=True,
                priority=100,
            )
        )

        # Rule 2: Critical risk escalation
        self.rules.append(
            EscalationRule(
                rule_id="critical_risk_escalation",
                rule_name="Critical Risk Escalation",
                escalation_type=EscalationType.HIGH_RISK,
                risk_levels=[RiskLevel.CRITICAL],
                target_role=self.config.critical_risk_escalation,
                send_email=True,
                send_sms=True,
                send_slack=True,
                priority=200,
            )
        )

        # Rule 3: High risk escalation
        self.rules.append(
            EscalationRule(
                rule_id="high_risk_escalation",
                rule_name="High Risk Escalation",
                escalation_type=EscalationType.HIGH_RISK,
                risk_levels=[RiskLevel.HIGH],
                target_role=self.config.high_risk_escalation,
                send_email=True,
                send_slack=True,
                priority=150,
            )
        )

        # Rule 4: Multiple rejections escalation
        self.rules.append(
            EscalationRule(
                rule_id="multiple_rejections",
                rule_name="Multiple Rejections Escalation",
                escalation_type=EscalationType.MULTIPLE_REJECTIONS,
                max_rejections=self.config.rejection_threshold,
                target_role="security_manager",
                send_email=True,
                send_slack=True,
                priority=120,
            )
        )

        self.logger.info("Initialized %d default escalation rules", len(self.rules))

    def add_rule(self, rule: EscalationRule) -> None:
        """
        Add custom escalation rule.

        Args:
            rule: Escalation rule to add
        """
        self.rules.append(rule)
        # Sort by priority (descending)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        self.logger.info("Added escalation rule: %s", rule.rule_name)

    def check_for_escalation(self, decision: HITLDecision) -> EscalationRule | None:
        """
        Check if decision should be escalated.

        Args:
            decision: Decision to check

        Returns:
            Matching escalation rule, or None
        """
        if not self.config.enabled:
            return None

        # Check rules in priority order
        for rule in self.rules:
            if rule.matches(decision):
                self.logger.info(
                    "Escalation rule matched: %s (decision=%s)", rule.rule_name, decision.decision_id
                )
                return rule

        return None
