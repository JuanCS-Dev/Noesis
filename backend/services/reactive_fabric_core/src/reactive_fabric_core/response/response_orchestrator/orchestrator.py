"""
Response Orchestrator for Reactive Fabric.

Coordinates automated responses to detected threats.
Phase 2: ACTIVE responses with safety controls.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List

from .action_handlers import ActionHandlersMixin
from .execution import ExecutionMixin
from .models import (
    ResponseAction,
    ResponseConfig,
    ResponsePlan,
    ResponsePriority,
    ResponseStatus,
    SafetyCheck,
)
from .planning import PlanningMixin


class ResponseOrchestrator(PlanningMixin, ExecutionMixin, ActionHandlersMixin):
    """Orchestrates automated responses to threats."""

    def __init__(self, config: ResponseConfig = None):
        """Initialize response orchestrator."""
        self.config = config or ResponseConfig()
        self.response_plans: Dict[str, ResponsePlan] = {}
        self.active_responses: Dict[str, ResponsePlan] = {}
        self.completed_responses: Dict[str, ResponsePlan] = {}
        self.action_history: List[ResponseAction] = []
        self.safety_checks: List[SafetyCheck] = []

        # Execution tracking
        self.executing_actions: set[str] = set()
        self.execution_semaphore = asyncio.Semaphore(
            self.config.max_concurrent_actions
        )

        # Metrics
        self.total_plans = 0
        self.total_actions = 0
        self.successful_actions = 0
        self.failed_actions = 0
        self.rollback_count = 0

        # Integration points (to be injected)
        self.firewall = None
        self.kill_switch = None
        self.network_segmentation = None
        self.data_diode = None

        self._running = False
        self._executor_task = None

    async def create_response_plan(
        self,
        threat_id: str,
        threat_score: float,
        threat_category: str,
        entities: Dict[str, Any],
        mitre_tactics: List[str] = None
    ) -> ResponsePlan:
        """Create a response plan for a detected threat."""
        # Determine priority based on threat score
        if threat_score >= self.config.critical_threshold:
            priority = ResponsePriority.CRITICAL
        elif threat_score >= self.config.high_threshold:
            priority = ResponsePriority.HIGH
        elif threat_score >= self.config.medium_threshold:
            priority = ResponsePriority.MEDIUM
        else:
            priority = ResponsePriority.LOW

        # Generate appropriate actions based on threat
        actions = await self._generate_response_actions(
            threat_category,
            entities,
            priority,
            mitre_tactics
        )

        # Determine execution order and parallel groups
        execution_order, parallel_groups = self._plan_execution_order(actions)

        # Create plan
        plan = ResponsePlan(
            name=f"Response to {threat_category}",
            description=f"Automated response plan for threat {threat_id}",
            threat_id=threat_id,
            threat_score=threat_score,
            actions=actions,
            execution_order=execution_order,
            parallel_groups=parallel_groups,
            priority=priority,
            auto_execute=(
                self.config.auto_response_enabled and
                priority in [ResponsePriority.CRITICAL, ResponsePriority.HIGH]
            ),
            require_confirmation=self.config.require_dual_approval
        )

        # Store plan
        self.response_plans[plan.plan_id] = plan
        self.total_plans += 1

        # Auto-execute if configured
        if plan.auto_execute and not plan.require_confirmation:
            await self.execute_plan(plan.plan_id)

        return plan

    async def execute_plan(
        self,
        plan_id: str,
        approver: str = None,
        skip_safety: bool = False
    ) -> bool:
        """Execute a response plan."""
        if plan_id not in self.response_plans:
            return False

        plan = self.response_plans[plan_id]

        # Safety checks
        if self.config.safety_checks_enabled and not skip_safety:
            checks_passed = await self._perform_safety_checks(plan)
            if not checks_passed:
                plan.status = ResponseStatus.CANCELLED
                return False

        # Mark as approved
        if approver:
            plan.approved_at = datetime.utcnow()

        # Move to active responses
        self.active_responses[plan_id] = plan
        plan.status = ResponseStatus.EXECUTING
        plan.executed_at = datetime.utcnow()

        # Execute actions according to plan
        success = await self._execute_actions(plan)

        # Update status
        if success:
            plan.status = ResponseStatus.COMPLETED
        else:
            plan.status = ResponseStatus.FAILED

            # Rollback if configured
            if self.config.rollback_on_failure:
                await self._rollback_plan(plan)

        plan.completed_at = datetime.utcnow()

        # Move to completed
        self.completed_responses[plan_id] = plan
        del self.active_responses[plan_id]

        return success

    async def _rollback_plan(self, plan: ResponsePlan) -> None:
        """Rollback executed actions."""
        plan.status = ResponseStatus.ROLLBACK
        self.rollback_count += 1

        # Rollback in reverse order
        for action_id in reversed(plan.executed_actions):
            action = next(
                (a for a in plan.actions if a.action_id == action_id),
                None
            )
            if action and action.reversible:
                await self._rollback_action(action)

    async def get_response_status(self) -> Dict[str, Any]:
        """Get current response status."""
        return {
            "active_plans": len(self.active_responses),
            "completed_plans": len(self.completed_responses),
            "executing_actions": len(self.executing_actions),
            "total_plans": self.total_plans,
            "total_actions": self.total_actions,
            "successful_actions": self.successful_actions,
            "failed_actions": self.failed_actions,
            "rollback_count": self.rollback_count,
            "recent_plans": [
                {
                    "plan_id": p.plan_id,
                    "name": p.name,
                    "status": p.status.value,
                    "priority": p.priority.value,
                    "threat_score": p.threat_score
                }
                for p in list(self.completed_responses.values())[-5:]
            ]
        }

    async def start(self) -> None:
        """Start response orchestrator."""
        self._running = True

    async def stop(self) -> None:
        """Stop response orchestrator."""
        self._running = False

        # Wait for executing actions to complete
        while self.executing_actions:
            await asyncio.sleep(0.1)

    def get_metrics(self) -> Dict[str, Any]:
        """Get orchestrator metrics."""
        return {
            "running": self._running,
            "total_plans": self.total_plans,
            "active_plans": len(self.active_responses),
            "completed_plans": len(self.completed_responses),
            "total_actions": self.total_actions,
            "successful_actions": self.successful_actions,
            "failed_actions": self.failed_actions,
            "success_rate": (
                self.successful_actions / self.total_actions
                if self.total_actions > 0 else 0
            ),
            "rollback_count": self.rollback_count,
            "safety_checks": len(self.safety_checks)
        }

    def __repr__(self) -> str:
        """String representation."""
        rate = (
            self.successful_actions / self.total_actions
            if self.total_actions > 0 else 0
        )
        return (
            f"ResponseOrchestrator(running={self._running}, "
            f"plans={self.total_plans}, "
            f"actions={self.total_actions}, "
            f"success_rate={rate:.2%})"
        )
