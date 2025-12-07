"""
Phase 5: Human-in-the-Loop Check.

Determines if action requires human review based on risk and confidence.
Target: <50ms

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from maximus_core_service.hitl import (
    ActionType,
    AutomationLevel,
    DecisionContext,
    RiskAssessor,
    RiskLevel,
)

from .models import HITLCheckResult

if TYPE_CHECKING:
    pass


async def hitl_check(
    risk_assessor: RiskAssessor,
    action: str,
    context: dict[str, Any],
    confidence_score: float = 0.0,
) -> HITLCheckResult:
    """
    Phase 5: HITL (Human-in-the-Loop) check.

    Determines if action requires human review based on:
    - Action risk level (from RiskAssessor)
    - Confidence score from previous phases
    - Automation level thresholds

    Target: <50ms

    Args:
        risk_assessor: RiskAssessor instance
        action: Action being validated
        context: Action context
        confidence_score: Confidence from ethics evaluation

    Returns:
        HITLCheckResult with automation level and review requirements
    """
    start_time = time.time()

    # Extract confidence from context or use provided score
    if confidence_score == 0.0:
        confidence_score = context.get("confidence", 0.0)

    # Map action string to ActionType
    try:
        action_lower = action.lower().replace(" ", "_")
        action_type = None
        for at in ActionType:
            if at.value == action_lower or at.value in action_lower:
                action_type = at
                break
        if action_type is None:
            action_type = ActionType.SEND_ALERT
    except Exception:
        action_type = ActionType.SEND_ALERT

    # Create DecisionContext for risk assessment
    decision_context = DecisionContext(
        action_type=action_type,
        action_params=context,
        confidence=confidence_score,
        threat_score=context.get("threat_score", 0.0),
        affected_assets=context.get("affected_assets", []),
        asset_criticality=context.get("asset_criticality", "medium"),
    )

    # Assess risk using RiskAssessor
    risk_score = risk_assessor.assess_risk(decision_context)

    # Determine automation level based on confidence and risk
    if confidence_score >= 0.95 and risk_score.risk_level == RiskLevel.LOW:
        automation_level = AutomationLevel.FULL
    elif confidence_score >= 0.80 and risk_score.risk_level in [
        RiskLevel.LOW,
        RiskLevel.MEDIUM,
    ]:
        automation_level = AutomationLevel.SUPERVISED
    elif confidence_score >= 0.60:
        automation_level = AutomationLevel.ADVISORY
    else:
        automation_level = AutomationLevel.MANUAL

    # Determine if human review is required
    requires_human_review = automation_level in [
        AutomationLevel.ADVISORY,
        AutomationLevel.MANUAL,
    ]

    # Confidence threshold check
    confidence_threshold_met = False
    if automation_level == AutomationLevel.FULL:
        confidence_threshold_met = confidence_score >= 0.95
    elif automation_level == AutomationLevel.SUPERVISED:
        confidence_threshold_met = confidence_score >= 0.80
    elif automation_level == AutomationLevel.ADVISORY:
        confidence_threshold_met = confidence_score >= 0.60
    else:
        confidence_threshold_met = False

    # Determine SLA based on risk level
    sla_mapping = {
        RiskLevel.CRITICAL: 5,
        RiskLevel.HIGH: 10,
        RiskLevel.MEDIUM: 15,
        RiskLevel.LOW: 30,
    }
    estimated_sla_minutes = sla_mapping.get(risk_score.risk_level, 15)

    # Recommend escalation for critical/high risk
    escalation_recommended = risk_score.risk_level in [
        RiskLevel.CRITICAL,
        RiskLevel.HIGH,
    ]

    # Determine required human expertise
    human_expertise_required = []
    if risk_score.risk_level == RiskLevel.CRITICAL:
        human_expertise_required = ["security_manager", "ciso"]
    elif risk_score.risk_level == RiskLevel.HIGH:
        human_expertise_required = ["soc_supervisor", "security_manager"]
    elif requires_human_review:
        human_expertise_required = ["soc_operator"]

    # Generate decision rationale
    decision_rationale = (
        f"Action '{action}' assessed as {risk_score.risk_level.value} risk with "
        f"{confidence_score:.1%} confidence. Automation level: {automation_level.value}. "
    )

    if requires_human_review:
        decision_rationale += f"Human review required (SLA: {estimated_sla_minutes}min)."
    else:
        decision_rationale += "Approved for autonomous execution."

    duration_ms = (time.time() - start_time) * 1000

    return HITLCheckResult(
        requires_human_review=requires_human_review,
        automation_level=automation_level.value,
        risk_level=risk_score.risk_level.value,
        confidence_threshold_met=confidence_threshold_met,
        estimated_sla_minutes=estimated_sla_minutes,
        escalation_recommended=escalation_recommended,
        human_expertise_required=human_expertise_required,
        decision_rationale=decision_rationale,
        duration_ms=duration_ms,
    )
