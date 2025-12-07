"""
Orchestration Mixin for Decision Framework.

Handles framework setup, dependency injection, and metrics.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..base_pkg import ActionType


class OrchestrationMixin:
    """
    Mixin for framework orchestration.

    Provides dependency injection and metrics collection.
    """

    def set_decision_queue(self, queue: Any) -> None:
        """
        Set decision queue instance.

        Args:
            queue: DecisionQueue instance
        """
        self._decision_queue = queue
        self.logger.info("Decision queue connected")

    def set_audit_trail(self, audit_trail: Any) -> None:
        """
        Set audit trail instance.

        Args:
            audit_trail: AuditTrail instance
        """
        self._audit_trail = audit_trail
        self.logger.info("Audit trail connected")

    def register_executor(self, action_type: ActionType, executor: Callable) -> None:
        """
        Register action executor function.

        Args:
            action_type: Type of action
            executor: Callable that executes the action
                     Signature: executor(context: DecisionContext) -> Dict[str, Any]
        """
        self._executors[action_type] = executor
        self.logger.info("Registered executor for %s", action_type.value)

    def get_metrics(self) -> dict[str, Any]:
        """
        Get framework metrics.

        Returns:
            Dictionary with decision metrics and rates
        """
        return {
            **self.metrics,
            "automation_rate": (
                self.metrics["auto_executed"] / self.metrics["total_decisions"]
                if self.metrics["total_decisions"] > 0
                else 0.0
            ),
            "human_review_rate": (
                self.metrics["queued_for_review"] / self.metrics["total_decisions"]
                if self.metrics["total_decisions"] > 0
                else 0.0
            ),
            "rejection_rate": (
                self.metrics["rejected"] / self.metrics["total_decisions"]
                if self.metrics["total_decisions"] > 0
                else 0.0
            ),
        }
