"""
Execution Mixin for Decision Framework.

Handles actual execution of security actions.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from ..base_pkg import DecisionStatus
from .models import DecisionResult

if TYPE_CHECKING:
    from ..base_pkg import DecisionContext, HITLDecision, OperatorAction


class ExecutionMixin:
    """
    Mixin for executing security actions.

    Provides immediate execution and operator-approved execution.
    """

    def _execute_immediately(self, decision: HITLDecision) -> DecisionResult:
        """
        Execute decision immediately (FULL automation).

        Args:
            decision: Decision to execute

        Returns:
            DecisionResult with execution status
        """
        try:
            # Execute action
            execution_output = self._execute_action(decision.context)

            # Update decision status
            decision.status = DecisionStatus.EXECUTED
            decision.executed_at = datetime.utcnow()
            decision.execution_result = execution_output

            # Log to audit trail
            if self._audit_trail:
                audit_entry = self._audit_trail.log_decision_executed(decision, execution_output)
                audit_entry_id = audit_entry.entry_id
            else:
                audit_entry_id = None

            result = DecisionResult(
                decision=decision,
                executed=True,
                execution_output=execution_output,
                audit_entry_id=audit_entry_id,
            )

            self.logger.info(
                "Decision executed: %s (action=%s)", decision.decision_id, decision.context.action_type.value
            )

            return result

        except Exception as e:
            # Execution failed
            self.logger.error(
                "Execution failed for %s: %s", decision.decision_id, e, exc_info=True
            )

            decision.status = DecisionStatus.FAILED
            decision.execution_error = str(e)

            # Log failure to audit trail
            if self._audit_trail:
                self._audit_trail.log_decision_failed(decision, str(e), {})

            return DecisionResult(
                decision=decision,
                executed=False,
                execution_error=str(e),
            )

    def execute_decision(
        self, decision: HITLDecision, operator_action: OperatorAction | None = None
    ) -> DecisionResult:
        """
        Execute a decision (after human approval).

        Args:
            decision: Decision to execute
            operator_action: Operator action (approval/modification)

        Returns:
            DecisionResult
        """
        self.logger.info(
            "Executing decision %s (action=%s)", decision.decision_id, decision.context.action_type.value
        )

        # Apply operator modifications if any
        if operator_action and operator_action.modifications:
            self.logger.info(
                "Applying operator modifications to %s: %s",
                decision.decision_id,
                operator_action.modifications,
            )
            decision.context.action_params.update(operator_action.modifications)

        # Log decision approval to audit trail
        if self._audit_trail and operator_action:
            self._audit_trail.log_decision_approved(decision, operator_action)

        # Execute
        try:
            execution_output = self._execute_action(decision.context)

            # Update decision
            decision.status = DecisionStatus.EXECUTED
            decision.executed_at = datetime.utcnow()
            decision.execution_result = execution_output

            # Log to audit trail
            if self._audit_trail:
                audit_entry = self._audit_trail.log_decision_executed(decision, execution_output)
                audit_entry_id = audit_entry.entry_id
            else:
                audit_entry_id = None

            result = DecisionResult(
                decision=decision,
                executed=True,
                execution_output=execution_output,
                audit_entry_id=audit_entry_id,
            )

            self.logger.info("Decision executed successfully: %s", decision.decision_id)
            return result

        except Exception as e:
            self.logger.error(
                "Execution failed for %s: %s", decision.decision_id, e, exc_info=True
            )

            decision.status = DecisionStatus.FAILED
            decision.execution_error = str(e)

            # Log failure
            if self._audit_trail:
                self._audit_trail.log_decision_failed(decision, str(e), {})

            return DecisionResult(
                decision=decision,
                executed=False,
                execution_error=str(e),
            )

    def _execute_action(self, context: DecisionContext) -> dict[str, Any]:
        """
        Execute security action.

        Args:
            context: Decision context with action details

        Returns:
            Execution result

        Raises:
            ValueError: If no executor registered for action type
            Exception: If execution fails
        """
        action_type = context.action_type

        # Get executor
        executor = self._executors.get(action_type)
        if executor is None:
            raise ValueError(f"No executor registered for action type: {action_type.value}")

        # Execute
        self.logger.debug("Executing %s with params: %s", action_type.value, context.action_params)

        result = executor(context)

        self.logger.debug("Execution complete: %s → %s", action_type.value, result)

        return result
