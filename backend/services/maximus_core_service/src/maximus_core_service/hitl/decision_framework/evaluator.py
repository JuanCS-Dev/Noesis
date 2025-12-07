"""
Action Evaluation Mixin for Decision Framework.

Main entry point for AI-proposed actions.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from ..base_pkg import AutomationLevel, DecisionStatus, HITLDecision
from .models import DecisionResult

if TYPE_CHECKING:
    from ..base_pkg import ActionType, DecisionContext


class ActionEvaluationMixin:
    """
    Mixin for evaluating AI-proposed actions.

    Orchestrates risk assessment, automation level determination, and decision routing.
    """

    def evaluate_action(
        self,
        action_type: ActionType,
        action_params: dict[str, Any],
        ai_reasoning: str,
        confidence: float,
        threat_score: float = 0.0,
        affected_assets: list[str] | None = None,
        **context_kwargs,
    ) -> DecisionResult:
        """
        Evaluate AI-proposed action and determine automation level.

        This is the main entry point for MAXIMUS AI to submit decisions.

        Args:
            action_type: Type of security action
            action_params: Parameters for the action
            ai_reasoning: AI's reasoning for the action
            confidence: AI's confidence score (0.0 to 1.0)
            threat_score: Threat severity score (0.0 to 1.0)
            affected_assets: List of affected asset IDs
            **context_kwargs: Additional context parameters

        Returns:
            DecisionResult indicating execution status
        """
        from ..base_pkg import DecisionContext

        start_time = datetime.utcnow()
        self.metrics["total_decisions"] += 1

        # Build decision context
        context = DecisionContext(
            action_type=action_type,
            action_params=action_params,
            ai_reasoning=ai_reasoning,
            confidence=confidence,
            threat_score=threat_score,
            affected_assets=affected_assets or [],
            **context_kwargs,
        )

        # Assess risk
        risk_score = self.risk_assessor.assess_risk(context)

        self.logger.info(
            "Risk assessment: %s (score=%.2f, confidence=%.2f, action=%s)",
            risk_score.risk_level.value,
            risk_score.overall_score,
            confidence,
            action_type.value,
        )

        # Determine automation level
        automation_level = self.config.get_automation_level(confidence, risk_score.risk_level)

        # Create HITL decision
        decision = HITLDecision(
            context=context,
            risk_level=risk_score.risk_level,
            automation_level=automation_level,
            status=DecisionStatus.PENDING,
        )

        # Set SLA deadline if requires review
        if decision.requires_human_review():
            sla_timeout = self.config.sla_config.get_timeout_delta(risk_score.risk_level)
            decision.sla_deadline = datetime.utcnow() + sla_timeout

        # Log decision creation to audit trail
        if self._audit_trail:
            audit_entry = self._audit_trail.log_decision_created(decision, risk_score)
            decision.metadata["audit_entry_id"] = audit_entry.entry_id

        # Process based on automation level
        result: DecisionResult

        if automation_level == AutomationLevel.FULL:
            # Execute immediately
            self.logger.info(
                "FULL automation: executing %s (decision=%s)", action_type.value, decision.decision_id
            )
            result = self._execute_immediately(decision)
            self.metrics["auto_executed"] += 1

        elif automation_level in [AutomationLevel.SUPERVISED, AutomationLevel.ADVISORY]:
            # Queue for human review
            self.logger.info(
                "%s automation: queueing %s for review (decision=%s)",
                automation_level.value.upper(),
                action_type.value,
                decision.decision_id,
            )
            result = self._queue_for_review(decision)
            self.metrics["queued_for_review"] += 1

        elif automation_level == AutomationLevel.MANUAL:
            # Manual only - no AI suggestion
            self.logger.info(
                "MANUAL automation: no AI execution for %s (decision=%s, confidence too low)",
                action_type.value,
                decision.decision_id,
            )
            decision.status = DecisionStatus.PENDING
            result = self._queue_for_review(decision)
            self.metrics["queued_for_review"] += 1

        else:
            raise ValueError(f"Unknown automation level: {automation_level}")

        # Record processing time
        end_time = datetime.utcnow()
        result.processing_time = (end_time - start_time).total_seconds()

        self.logger.info(
            "Decision evaluated: %s → %s (processing_time=%.3fs)",
            decision.decision_id,
            automation_level.value,
            result.processing_time,
        )

        return result
