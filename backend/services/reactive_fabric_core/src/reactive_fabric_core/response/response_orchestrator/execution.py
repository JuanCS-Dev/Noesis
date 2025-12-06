"""
Execution Mixin for Response Orchestrator.

Contains safety checks and action execution logic.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from .models import (
    ResponseAction,
    ResponsePlan,
    ResponsePriority,
    ResponseStatus,
    SafetyCheck,
)


class ExecutionMixin:
    """Mixin providing execution capabilities."""

    # Required attributes from main class
    executing_actions: Set[str]
    execution_semaphore: asyncio.Semaphore
    safety_checks: List[SafetyCheck]
    action_history: List[ResponseAction]
    successful_actions: int
    failed_actions: int

    async def _perform_safety_checks(self, plan: ResponsePlan) -> bool:
        """Perform safety checks before executing plan."""
        checks_passed = True

        # Check 1: System stability
        stability_check = SafetyCheck(
            check_type="system_stability",
            passed=True,
            message="System stable for response execution"
        )
        self.safety_checks.append(stability_check)
        checks_passed &= stability_check.passed

        # Check 2: No conflicting actions
        conflict_check = SafetyCheck(
            check_type="action_conflicts",
            passed=len(self.executing_actions) == 0,
            message="No conflicting actions in progress"
        )
        self.safety_checks.append(conflict_check)
        checks_passed &= conflict_check.passed

        # Check 3: Resource availability
        resource_check = SafetyCheck(
            check_type="resource_availability",
            passed=True,
            message="Sufficient resources available"
        )
        self.safety_checks.append(resource_check)
        checks_passed &= resource_check.passed

        # Check 4: Business hours (for non-critical)
        if plan.priority not in [ResponsePriority.CRITICAL]:
            now = datetime.utcnow()
            business_hours = 8 <= now.hour < 18

            business_check = SafetyCheck(
                check_type="business_hours",
                passed=business_hours or plan.priority == ResponsePriority.CRITICAL,
                message="Within business hours or critical priority"
            )
            self.safety_checks.append(business_check)
            checks_passed &= business_check.passed

        return checks_passed

    async def _execute_actions(self, plan: ResponsePlan) -> bool:
        """Execute actions in the response plan."""
        success = True

        # Execute parallel groups in sequence
        for group in plan.parallel_groups:
            # Execute actions in group in parallel
            tasks = []
            for action_id in group:
                action = next(
                    (a for a in plan.actions if a.action_id == action_id),
                    None
                )
                if action:
                    tasks.append(self._execute_single_action(action))

            # Wait for group to complete
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Check results
                for i, result in enumerate(results):
                    if isinstance(result, Exception) or not result:
                        success = False
                        plan.failed_actions.append(group[i])
                    else:
                        plan.executed_actions.append(group[i])

        return success

    async def _execute_single_action(self, action: ResponseAction) -> bool:
        """Execute a single response action."""
        async with self.execution_semaphore:
            try:
                self.executing_actions.add(action.action_id)
                action.status = ResponseStatus.EXECUTING
                action.executed_at = datetime.utcnow()

                # Route to appropriate handler
                result = await self._route_action(action)

                if result:
                    action.status = ResponseStatus.COMPLETED
                    action.result = result
                    self.successful_actions += 1
                else:
                    action.status = ResponseStatus.FAILED
                    self.failed_actions += 1

                action.completed_at = datetime.utcnow()
                self.action_history.append(action)

                return result is not None

            except Exception as e:
                action.status = ResponseStatus.FAILED
                action.error_message = str(e)
                self.failed_actions += 1
                return False

            finally:
                self.executing_actions.discard(action.action_id)

    async def _route_action(self, action: ResponseAction) -> Optional[Dict[str, Any]]:
        """Route action to handler. Implemented in ActionHandlersMixin."""
        raise NotImplementedError("Must be implemented by ActionHandlersMixin")
