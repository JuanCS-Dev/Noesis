"""
Core Escalation Manager Implementation.

Main escalation manager combining all mixins.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from ..base_pkg import EscalationConfig
from .escalation import EscalationExecutionMixin
from .metrics import MetricsHistoryMixin
from .models import EscalationEvent, EscalationRule
from .notifications import NotificationMixin
from .rules import EscalationRulesMixin


class EscalationManager(
    EscalationRulesMixin,
    EscalationExecutionMixin,
    NotificationMixin,
    MetricsHistoryMixin,
):
    """
    Manages decision escalation to higher authority.

    Monitors decisions for escalation triggers and automatically escalates
    based on configured rules.

    Inherits from:
        - EscalationRulesMixin: _initialize_default_rules, add_rule, check_for_escalation
        - EscalationExecutionMixin: escalate_decision, get_escalation_target
        - NotificationMixin: register_notification_handler, _send_notifications
        - MetricsHistoryMixin: get_metrics, get_escalation_history
    """

    def __init__(self, config: EscalationConfig | None = None) -> None:
        """
        Initialize escalation manager.

        Args:
            config: Escalation configuration
        """
        self.config = config or EscalationConfig()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Escalation rules
        self.rules: list[EscalationRule] = []
        self._initialize_default_rules()

        # Escalation history
        self.escalation_history: list[EscalationEvent] = []

        # Notification handlers
        self._notification_handlers: dict[str, Callable] = {}

        # Metrics
        self.metrics = {
            "total_escalations": 0,
            "timeout_escalations": 0,
            "risk_escalations": 0,
            "rejection_escalations": 0,
            "operator_escalations": 0,
        }

        self.logger.info("Escalation Manager initialized")
