"""
Core HITL Decision Framework Implementation.

Main decision framework combining all mixins.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from ..base_pkg import ActionType, HITLConfig
from ..risk_assessor import RiskAssessor
from .evaluator import ActionEvaluationMixin
from .executor import ExecutionMixin
from .helpers import HelperMethodsMixin
from .operator import OperatorIntegrationMixin
from .orchestration import OrchestrationMixin
from .queuing import ReviewQueueingMixin


class HITLDecisionFramework(
    ActionEvaluationMixin,
    ExecutionMixin,
    ReviewQueueingMixin,
    OperatorIntegrationMixin,
    OrchestrationMixin,
    HelperMethodsMixin,
):
    """
    Main HITL decision framework.

    Coordinates risk assessment, automation level determination, decision
    queueing, and execution for AI-proposed security actions.

    Inherits from:
        - ActionEvaluationMixin: evaluate_action (main entry point)
        - ExecutionMixin: _execute_immediately, execute_decision, _execute_action
        - ReviewQueueingMixin: _queue_for_review
        - OperatorIntegrationMixin: reject_decision, escalate_decision
        - OrchestrationMixin: register_executor, set_decision_queue, set_audit_trail, get_metrics
        - HelperMethodsMixin: block_ip, isolate_host, quarantine_file, kill_process
    """

    def __init__(
        self,
        config: HITLConfig | None = None,
        risk_assessor: RiskAssessor | None = None,
    ) -> None:
        """
        Initialize HITL framework.

        Args:
            config: HITL configuration
            risk_assessor: Risk assessment engine (created if not provided)
        """
        self.config = config or HITLConfig()
        self.risk_assessor = risk_assessor or RiskAssessor()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Action executors (registered by action type)
        self._executors: dict[ActionType, Callable] = {}

        # Decision queue (will be set by DecisionQueue)
        self._decision_queue: Any | None = None

        # Audit trail (will be set by AuditTrail)
        self._audit_trail: Any | None = None

        # Metrics
        self.metrics = {
            "total_decisions": 0,
            "auto_executed": 0,
            "queued_for_review": 0,
            "rejected": 0,
            "escalated": 0,
        }

        self.logger.info("HITL Decision Framework initialized")
