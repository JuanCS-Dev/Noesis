"""
HCL Planner Service - Agentic Planner
=====================================

Meta-cognitive infrastructure planner powered by Gemini 3 Pro.

This module implements the core planning logic for the Homeostatic Control Loop (HCL).
It uses Gemini 3 Pro's thinking mode to perform deep reasoning before generating plans.

Features:
    - Meta-cognitive thought tracing
    - Self-correcting plan generation
    - Action catalog management
    - Dependency injection support

Example:
    >>> from config import get_settings
    >>> settings = get_settings()
    >>> planner = AgenticPlanner(settings.gemini)
    >>> actions = await planner.recommend_actions(state, analysis, goals)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, cast

from config import GeminiSettings
from core.gemini_client import GeminiClient, GeminiAPIError
from core.action_catalog import get_action_catalog
from utils.logging_config import get_logger

logger = get_logger(__name__)


class PlannerNotAvailableError(Exception):
    """Raised when planner cannot be used (e.g., no API key)."""


class AgenticPlanner:
    """
    GenAI-driven planner using Gemini 3 Pro for infrastructure decisions.

    Analyzes system state and operational goals to recommend infrastructure
    actions. Uses meta-cognitive reasoning for robust decision-making.

    Attributes:
        client: Gemini API client (None if disabled)
        action_catalog: Available infrastructure actions
    """

    def __init__(
        self,
        gemini_config: GeminiSettings,
        action_catalog: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Initialize Agentic Planner.

        Args:
            gemini_config: Gemini configuration
            action_catalog: Custom action catalog (uses default if None)

        Note:
            If gemini_config.api_key is None, planner will be disabled
            and all recommend_actions calls will raise PlannerNotAvailableError.
        """
        self.action_catalog = action_catalog or get_action_catalog()

        if not gemini_config.api_key:
            logger.warning(
                "planner_disabled",
                extra={"reason": "no_api_key"}
            )
            self.client: Optional[GeminiClient] = None
        else:
            try:
                self.client = GeminiClient(gemini_config)
                logger.info(
                    "agentic_planner_initialized",
                    extra={
                        "model": gemini_config.model,
                        "thinking_level": gemini_config.thinking_level,
                        "action_count": len(self.action_catalog)
                    }
                )
            except ValueError as e:
                logger.error(
                    "planner_initialization_failed",
                    extra={"error": str(e)}
                )
                self.client = None

    async def recommend_actions(
        self,
        current_state: Dict[str, Any],
        analysis_result: Dict[str, Any],
        operational_goals: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Generate recommended infrastructure actions.

        Combines current state and analysis to create a full system context,
        then uses Gemini to generate action recommendations.

        Args:
            current_state: Raw system metrics
            analysis_result: Analysis insights from HCL Analyzer
            operational_goals: Desired operational outcomes

        Returns:
            List of recommended actions, each containing:
                - type (str): Action type
                - parameters (dict): Action parameters

        Raises:
            PlannerNotAvailableError: If planner is disabled
            GeminiAPIError: If Gemini API fails

        Example:
            >>> actions = await planner.recommend_actions(
            ...     current_state={"cpu_usage": 0.85},
            ...     analysis_result={"bottleneck": "cpu"},
            ...     operational_goals={"target_cpu": 0.70}
            ... )
            >>> print(actions[0]["type"])
            "scale_deployment"
        """
        if not self.client:
            raise PlannerNotAvailableError(
                "Planner is disabled (no Gemini API key). "
                "Set GEMINI_API_KEY environment variable."
            )

        logger.info(
            "planning_started",
            extra={"thinking_mode": "enabled"}
        )

        # Combine state and analysis for full context
        full_system_context = {
            "raw_metrics": current_state,
            "analysis_insights": analysis_result
        }

        try:
            plan = await self.client.generate_plan(
                system_state=full_system_context,
                operational_goals=operational_goals,
                available_actions=self.action_catalog
            )

            actions = plan.get("actions", [])
            reasoning = plan.get("reasoning", "No reasoning provided.")
            thought_trace = plan.get("thought_trace", "No thought trace.")

            # Log meta-cognitive process
            logger.info(
                "thought_trace_generated",
                extra={
                    "thought_trace": thought_trace,
                    "reasoning": reasoning
                }
            )

            logger.info(
                "planning_completed",
                extra={"action_count": len(actions)}
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

                # Use global client (started at service init)
                reflector = PrioritizedReflectorClient()

                log = ExecutionLog(
                    trace_id=f"plan-{uuid4().hex[:8]}",
                    agent_id="hcl_planner",
                    task=f"Generate plan for goals: {operational_goals}",
                    action=f"Recommended {len(actions)} actions",
                    outcome="Success" if actions else "No actions generated",
                    reasoning_trace=reasoning,
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

            return cast(List[Dict[str, Any]], actions)

        except GeminiAPIError as e:
            logger.error(
                "planning_failed",
                extra={"error": str(e)},
                exc_info=True
            )
            raise

    async def get_status(self) -> Dict[str, Any]:
        """
        Get planner health status.

        Returns:
            Dictionary containing:
                - status (str): "active" or "disabled"
                - model (str): Gemini model name or "N/A"
                - type (str): Planner type identifier
                - thinking_level (str): Thinking mode level or "N/A"
                - action_catalog_size (int): Number of available actions

        Example:
            >>> status = await planner.get_status()
            >>> assert status["status"] == "active"
        """
        if not self.client:
            return {
                "status": "disabled",
                "reason": "no_api_key",
                "model": "N/A",
                "type": "Agentic (Gemini 3.0 Pro)",
                "thinking_level": "N/A",
                "action_catalog_size": len(self.action_catalog)
            }

        return {
            "status": "active",
            "model": self.client.config.model,
            "type": "Agentic (Gemini 3.0 Pro)",
            "thinking_level": self.client.config.thinking_level,
            "action_catalog_size": len(self.action_catalog)
        }
