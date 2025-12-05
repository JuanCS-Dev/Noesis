"""
HITL Escalation Manager Package.

Manages escalation of decisions to higher authority based on:
- SLA timeout
- Risk level
- Multiple rejections
- Explicit operator escalation

Escalation Chain:
    soc_operator → soc_supervisor → security_manager → ciso

Notifications:
- Email for all escalations
- SMS for critical escalations
- Slack/Teams for team awareness

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Refactored: 2025-12-03
"""

from __future__ import annotations

# Core classes
from .core import EscalationManager
from .enums import EscalationType
from .models import EscalationEvent, EscalationRule

# Mixins (for advanced usage)
from .escalation import EscalationExecutionMixin
from .metrics import MetricsHistoryMixin
from .notifications import NotificationMixin
from .rules import EscalationRulesMixin

__all__ = [
    # Main classes
    "EscalationManager",
    "EscalationType",
    "EscalationRule",
    "EscalationEvent",
    # Mixins
    "EscalationRulesMixin",
    "EscalationExecutionMixin",
    "NotificationMixin",
    "MetricsHistoryMixin",
]
