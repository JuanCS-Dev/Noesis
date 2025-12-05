"""
Phase 2: XAI Explanation Generation.

Generates explainable AI explanations for decisions.
Target: <200ms

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from xai import DetailLevel, ExplanationEngine, ExplanationType

from .models import EthicsCheckResult, XAICheckResult

if TYPE_CHECKING:
    pass


async def generate_explanation(
    xai_engine: ExplanationEngine,
    action: str,
    context: dict[str, Any],
    ethics_result: EthicsCheckResult,
) -> XAICheckResult:
    """
    Phase 2: Generate XAI explanation.

    Target: <200ms

    Args:
        xai_engine: ExplanationEngine instance
        action: Action being validated
        context: Action context
        ethics_result: Result from ethics evaluation

    Returns:
        XAICheckResult with explanation
    """
    start_time = time.time()

    # Prepare input for XAI
    xai_input = {
        "action": action,
        "verdict": ethics_result.verdict.value,
        "confidence": ethics_result.confidence,
        "risk_score": context.get("risk_score", 0.5),
        "frameworks": [r["name"] for r in ethics_result.framework_results],
    }

    # Generate explanation
    # Note: For ethical decisions, we don't have an ML model, so we pass None
    explanation = await xai_engine.explain(
        model=None,
        instance=xai_input,
        prediction=ethics_result.verdict.value,
        explanation_type=ExplanationType.LIME,
        detail_level=DetailLevel.TECHNICAL,
    )

    # Extract feature importances
    feature_importances = [
        {"feature": f.feature_name, "importance": f.importance}
        for f in explanation.feature_importances[:5]
    ]

    duration_ms = (time.time() - start_time) * 1000

    return XAICheckResult(
        explanation_type=explanation.explanation_type.value,
        summary=explanation.summary,
        feature_importances=feature_importances,
        duration_ms=duration_ms,
    )
