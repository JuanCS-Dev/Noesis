"""
HITL Decision Queue Package.

Priority queue for decisions awaiting human review. Manages:
- Priority-based queueing (CRITICAL > HIGH > MEDIUM > LOW)
- SLA monitoring and timeout detection
- Operator assignment (round-robin or manual)
- Queue metrics and statistics

Queue Structure:
    CRITICAL queue (SLA: 5min)
    HIGH queue (SLA: 10min)
    MEDIUM queue (SLA: 15min)
    LOW queue (SLA: 30min)

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Refactored: 2025-12-03
"""

from __future__ import annotations

# Core classes
from .core import DecisionQueue
from .models import QueuedDecision
from .sla_monitor import SLAMonitor

# Mixins (for advanced usage)
from .metrics import MetricsMixin
from .operator_assignment import OperatorAssignmentMixin
from .priority import PriorityMixin
from .queue_management import QueueManagementMixin
from .sla_callbacks import SLACallbacksMixin

__all__ = [
    # Main classes
    "DecisionQueue",
    "QueuedDecision",
    "SLAMonitor",
    # Mixins
    "QueueManagementMixin",
    "OperatorAssignmentMixin",
    "PriorityMixin",
    "MetricsMixin",
    "SLACallbacksMixin",
]
