"""
HITL Decision Framework Package.

Core framework for human-in-the-loop security decisions.

This package orchestrates risk assessment, automation level determination,
decision queueing, and execution for AI-proposed security actions.

Workflow:
    1. AI proposes action → evaluate_action()
    2. Assess risk → RiskAssessor
    3. Determine automation level based on confidence + risk
    4. FULL automation? → Execute immediately + audit
    5. Requires review? → Queue for operator
    6. Operator reviews → approve/reject/escalate
    7. Execute approved actions → audit trail

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Refactored: 2025-12-03
"""

from __future__ import annotations

# Core framework
from .core import HITLDecisionFramework

# Data models
from .models import DecisionResult

# Mixins (for advanced usage)
from .evaluator import ActionEvaluationMixin
from .executor import ExecutionMixin
from .helpers import HelperMethodsMixin
from .operator import OperatorIntegrationMixin
from .orchestration import OrchestrationMixin
from .queuing import ReviewQueueingMixin

__all__ = [
    # Main classes
    "HITLDecisionFramework",
    "DecisionResult",
    # Mixins
    "ActionEvaluationMixin",
    "ExecutionMixin",
    "ReviewQueueingMixin",
    "OperatorIntegrationMixin",
    "OrchestrationMixin",
    "HelperMethodsMixin",
]
