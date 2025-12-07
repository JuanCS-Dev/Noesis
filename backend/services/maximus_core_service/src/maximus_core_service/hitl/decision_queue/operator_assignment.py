"""
Operator Assignment Mixin for Decision Queue.

Handles operator assignment and round-robin scheduling.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..base_pkg import HITLDecision


class OperatorAssignmentMixin:
    """
    Mixin for operator assignment operations.

    Handles assigning decisions to operators and tracking assignments.
    """

    def assign_to_operator(self, decision: HITLDecision, operator_id: str) -> None:
        """
        Assign decision to operator.

        Args:
            decision: Decision to assign
            operator_id: Operator ID
        """
        self._assign_to_operator(decision, operator_id)

    def _assign_to_operator(self, decision: HITLDecision, operator_id: str) -> None:
        """
        Internal assignment method.

        Args:
            decision: Decision to assign
            operator_id: Operator ID
        """
        decision.assigned_operator = operator_id
        decision.assigned_at = datetime.utcnow()

        # Track assignment
        if operator_id not in self._operator_assignments:
            self._operator_assignments[operator_id] = []
        self._operator_assignments[operator_id].append(decision.decision_id)

        # Add operator to set
        self._operators.add(operator_id)

        # Update metrics
        self.metrics["total_assigned"] += 1

        self.logger.info("Decision assigned: %s → %s", decision.decision_id, operator_id)

    def get_next_operator_round_robin(self) -> str | None:
        """
        Get next operator using round-robin assignment.

        Returns:
            Operator ID, or None if no operators registered
        """
        if not self._operators:
            return None

        operators = sorted(list(self._operators))
        operator = operators[self._current_operator_index % len(operators)]
        self._current_operator_index += 1

        return operator
