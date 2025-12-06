"""
HCL Executor Service - Action Executor
======================================

Core logic for executing infrastructure actions.
"""

import asyncio
import time
from typing import Any, Dict, List

from .k8s import KubernetesController
from ..models.actions import Action, ActionResult
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class ActionExecutor:
    """
    Executes infrastructure actions.

    Translates high-level actions into concrete Kubernetes operations.
    """

    def __init__(self, k8s_controller: KubernetesController):
        """
        Initialize ActionExecutor.

        Args:
            k8s_controller: Initialized Kubernetes controller
        """
        self.k8s_controller = k8s_controller
        logger.info("action_executor_initialized")

    async def execute_actions(
        self,
        plan_id: str,
        actions: List[Action]
    ) -> List[ActionResult]:
        """
        Execute a list of actions.

        Args:
            plan_id: ID of the plan containing these actions
            actions: List of Action objects to execute

        Returns:
            List of ActionResult objects
        """
        logger.info(
            "executing_plan_actions",
            extra={"plan_id": plan_id, "action_count": len(actions)}
        )

        results = []
        for action in actions:
            result = await self._execute_single_action(action)
            results.append(result)

            # Small delay to prevent API throttling
            await asyncio.sleep(0.05)

        return results

    async def _execute_single_action(self, action: Action) -> ActionResult:
        """
        Execute a single action.

        Args:
            action: Action to execute

        Returns:
            ActionResult object
        """
        result = None
        try:
            if action.type == "scale_deployment":
                result = await self._handle_scale_deployment(action)
            elif action.type == "update_resource_limits":
                result = await self._handle_update_limits(action)
            elif action.type == "restart_pod":
                result = await self._handle_restart_pod(action)
            else:
                logger.warning(
                    "unsupported_action_type",
                    extra={"type": action.type}
                )
                result = ActionResult(
                    action_type=action.type,
                    status="failed",
                    details=f"Unsupported action type: {action.type}",
                    timestamp=time.time()
                )

        except Exception as e:  # pylint: disable=broad-except
            logger.exception(
                "action_execution_error",
                extra={"type": action.type, "error": str(e)}
            )
            result = ActionResult(
                action_type=action.type,
                status="failed",
                details=str(e),
                timestamp=time.time()
            )

        # NEW: Metacognitive Reflection (Async)
        try:
            from datetime import datetime
            from uuid import uuid4
            from ...shared.reflector_client import (
                PrioritizedReflectorClient,
                ReflectionPriority
            )
            from ...metacognitive_reflector.models.reflection import ExecutionLog

            reflector = PrioritizedReflectorClient()
            
            log = ExecutionLog(
                trace_id=f"exec-{uuid4().hex[:8]}",
                agent_id="hcl_executor",
                task=f"Execute action: {action.get('type', 'unknown')}",
                action=f"Executed with outcome: {result.outcome}",
                outcome=result.outcome,
                reasoning_trace=str(result.details),
                timestamp=datetime.now()
            )

            # Async submission (non-blocking, HIGH priority)
            await reflector.submit_log_async(
                log,
                priority=ReflectionPriority.HIGH
            )
            
            logger.debug(
                "reflection_submitted_async",
                extra={"trace_id": log.trace_id}
            )

        except Exception as e:
            # Don't block on reflection failure
            logger.warning(
                "reflection_failed",
                extra={"error": str(e)}
            )
            # Continue despite reflection failure

        return result

    async def _handle_scale_deployment(self, action: Action) -> ActionResult:
        """Handle scale_deployment action."""
        params = action.parameters
        if not params.deployment_name or params.replicas is None:
            raise ValueError("Missing deployment_name or replicas")

        success = await self.k8s_controller.scale_deployment(
            params.deployment_name,
            params.namespace,
            params.replicas
        )

        status = "success" if success else "failed"
        details = (
            f"Scaled {params.deployment_name} to {params.replicas}"
            if success else "Failed to scale deployment"
        )

        return ActionResult(
            action_type=action.type,
            status=status,
            details=details,
            timestamp=time.time()
        )

    async def _handle_update_limits(self, action: Action) -> ActionResult:
        """Handle update_resource_limits action."""
        params = action.parameters
        if not params.deployment_name or (not params.cpu_limit and not params.memory_limit):
            raise ValueError("Missing deployment_name or limits")

        success = await self.k8s_controller.update_resource_limits(
            params.deployment_name,
            params.namespace,
            params.cpu_limit,
            params.memory_limit
        )

        status = "success" if success else "failed"
        details = (
            f"Updated limits for {params.deployment_name}"
            if success else "Failed to update limits"
        )

        return ActionResult(
            action_type=action.type,
            status=status,
            details=details,
            timestamp=time.time()
        )

    async def _handle_restart_pod(self, action: Action) -> ActionResult:
        """Handle restart_pod action."""
        params = action.parameters
        if not params.pod_name:
            raise ValueError("Missing pod_name")

        success = await self.k8s_controller.restart_pod(
            params.pod_name,
            params.namespace
        )

        status = "success" if success else "failed"
        details = (
            f"Restarted pod {params.pod_name}"
            if success else "Failed to restart pod"
        )

        return ActionResult(
            action_type=action.type,
            status=status,
            details=details,
            timestamp=time.time()
        )

    async def get_status(self) -> Dict[str, Any]:
        """Get executor status."""
        return {
            "status": "active",
            "timestamp": time.time()
        }
