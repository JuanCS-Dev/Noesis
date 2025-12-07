"""
Phase 1: Ethics Evaluation.

Evaluates action with 4 ethical frameworks.
Target: <200ms

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from maximus_core_service.ethics import ActionContext, EthicalIntegrationEngine, EthicalVerdict

from .models import EthicsCheckResult

if TYPE_CHECKING:
    pass


async def ethics_evaluation(
    ethics_engine: EthicalIntegrationEngine,
    action: str,
    context: dict[str, Any],
    actor: str,
) -> EthicsCheckResult:
    """
    Phase 1: Evaluate with 4 ethical frameworks.

    Target: <200ms

    Args:
        ethics_engine: EthicalIntegrationEngine instance
        action: Action being validated
        context: Action context
        actor: Actor performing action

    Returns:
        EthicsCheckResult with verdict and confidence
    """
    start_time = time.time()

    # Create action context
    action_ctx = ActionContext(
        action_type=action,
        action_description=f"MAXIMUS action: {action}",
        system_component=actor,
        target_info={"target": context.get("target", "unknown")},
        threat_data=context.get("threat_data"),
        impact_assessment={"risk_score": context.get("risk_score", 0.5)},
    )

    # Evaluate
    ethical_decision = await ethics_engine.evaluate(action_ctx)

    # Map final_decision string to EthicalVerdict enum
    verdict_map = {
        "APPROVED": EthicalVerdict.APPROVED,
        "REJECTED": EthicalVerdict.REJECTED,
        "CONDITIONAL": EthicalVerdict.CONDITIONAL,
        "ESCALATED_HITL": EthicalVerdict.CONDITIONAL,
    }
    verdict = verdict_map.get(ethical_decision.final_decision, EthicalVerdict.REJECTED)

    # Extract framework results (dict -> list)
    framework_results = [
        {
            "name": framework_name,
            "verdict": result.verdict if hasattr(result, "verdict") else "UNKNOWN",
            "score": result.confidence if hasattr(result, "confidence") else 0.0,
        }
        for framework_name, result in ethical_decision.framework_results.items()
    ]

    duration_ms = (time.time() - start_time) * 1000

    return EthicsCheckResult(
        verdict=verdict,
        confidence=ethical_decision.final_confidence,
        framework_results=framework_results,
        duration_ms=duration_ms,
    )
