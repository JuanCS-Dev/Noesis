"""
Notification Handling Mixin.

Handles sending escalation notifications via email, SMS, and Slack.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from .models import EscalationEvent, EscalationRule

if TYPE_CHECKING:
    from ..base_pkg import HITLDecision, RiskLevel


class NotificationMixin:
    """
    Mixin for notification handling.

    Sends escalation notifications via multiple channels.
    """

    def register_notification_handler(self, channel: str, handler: Callable) -> None:
        """
        Register notification handler.

        Args:
            channel: Notification channel ("email", "sms", "slack")
            handler: Handler function (decision, event) -> None
        """
        self._notification_handlers[channel] = handler
        self.logger.info("Registered notification handler for %s", channel)

    def _send_notifications(
        self,
        decision: HITLDecision,
        event: EscalationEvent,
        rule: EscalationRule | None = None,
    ) -> None:
        """
        Send escalation notifications.

        Args:
            decision: Decision being escalated
            event: Escalation event
            rule: Escalation rule (optional)
        """
        # Determine which notifications to send
        send_email = rule.send_email if rule else self.config.send_email
        send_sms = rule.send_sms if rule else self.config.send_sms
        send_slack = rule.send_slack if rule else self.config.send_slack

        # Email notification
        if send_email:
            event.email_sent = self._send_email_notification(decision, event)

        # SMS notification (for critical only)
        from ..base_pkg import RiskLevel

        if send_sms and decision.risk_level == RiskLevel.CRITICAL:
            event.sms_sent = self._send_sms_notification(decision, event)

        # Slack notification
        if send_slack:
            event.slack_sent = self._send_slack_notification(decision, event)

    def _send_email_notification(self, decision: HITLDecision, event: EscalationEvent) -> bool:
        """
        Send email notification.

        Args:
            decision: Decision being escalated
            event: Escalation event

        Returns:
            True if sent successfully
        """
        handler = self._notification_handlers.get("email")
        if handler:
            try:
                handler(decision, event)
                self.logger.info("Email notification sent for escalation %s", event.event_id)
                return True
            except Exception as e:
                self.logger.error("Failed to send email notification: %s", e)
                return False
        else:
            self.logger.debug("No email handler registered")
            return False

    def _send_sms_notification(self, decision: HITLDecision, event: EscalationEvent) -> bool:
        """
        Send SMS notification.

        Args:
            decision: Decision being escalated
            event: Escalation event

        Returns:
            True if sent successfully
        """
        handler = self._notification_handlers.get("sms")
        if handler:
            try:
                handler(decision, event)
                self.logger.info("SMS notification sent for escalation %s", event.event_id)
                return True
            except Exception as e:
                self.logger.error("Failed to send SMS notification: %s", e)
                return False
        else:
            self.logger.debug("No SMS handler registered")
            return False

    def _send_slack_notification(self, decision: HITLDecision, event: EscalationEvent) -> bool:
        """
        Send Slack notification.

        Args:
            decision: Decision being escalated
            event: Escalation event

        Returns:
            True if sent successfully
        """
        handler = self._notification_handlers.get("slack")
        if handler:
            try:
                handler(decision, event)
                self.logger.info("Slack notification sent for escalation %s", event.event_id)
                return True
            except Exception as e:
                self.logger.error("Failed to send Slack notification: %s", e)
                return False
        else:
            self.logger.debug("No Slack handler registered")
            return False
