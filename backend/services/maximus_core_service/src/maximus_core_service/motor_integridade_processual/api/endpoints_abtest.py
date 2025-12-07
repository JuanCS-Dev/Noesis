"""
A/B Testing Endpoints.

Endpoints for comparing CBR vs framework evaluation.

Author: Juan Carlos de Souza
Date: 2025-10-06
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status

from maximus_core_service.motor_integridade_processual.models.verdict import DecisionLevel

from .models import (
    ABTestMetricsResponse,
    ABTestResult,
    EvaluationRequest,
)
from .state import (
    ab_test_results,
    cbr_engine,
    cbr_validators,
    frameworks,
    resolver,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/evaluate/ab-test", response_model=dict[str, Any], status_code=status.HTTP_200_OK
)
async def evaluate_ab_test(request: EvaluationRequest) -> dict[str, Any]:
    """A/B test: Compare CBR vs Frameworks for same action plan."""
    start_time = time.time()

    # === Run CBR evaluation ===
    cbr_decision = None
    cbr_confidence = None
    cbr_time_ms = 0.0

    if cbr_engine is not None:
        cbr_start = time.time()
        try:
            case_dict = {
                "objective": request.action_plan.objective,
                "action_type": getattr(request.action_plan, "action_type", "unknown"),
                "context": getattr(request.action_plan, "context", {}),
            }

            cbr_result = await cbr_engine.full_cycle(case_dict, validators=cbr_validators)

            if cbr_result:
                action_map = {
                    "approve": DecisionLevel.APPROVE,
                    "approve_with_monitoring": DecisionLevel.APPROVE_WITH_CONDITIONS,
                    "escalate": DecisionLevel.ESCALATE_TO_HITL,
                    "reject": DecisionLevel.REJECT,
                }
                cbr_decision = action_map.get(
                    cbr_result.suggested_action, DecisionLevel.ESCALATE_TO_HITL
                ).value
                cbr_confidence = cbr_result.confidence

        except Exception as e:
            logger.warning(f"CBR evaluation failed in A/B test: {e}")

        cbr_time_ms = (time.time() - cbr_start) * 1000

    # === Run Framework evaluation ===
    framework_start = time.time()

    framework_verdicts = []
    for name, framework in frameworks.items():
        try:
            verdict = framework.evaluate(request.action_plan)
            framework_verdicts.append(verdict)
        except Exception as e:
            logger.error(f"Framework {name.value} failed in A/B test: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Framework evaluation failed: {str(e)}",
            )

    framework_verdict = resolver.resolve(framework_verdicts, request.action_plan)
    framework_time_ms = (time.time() - framework_start) * 1000

    # === Compare results ===
    decisions_match = (
        cbr_decision == framework_verdict.final_decision.value if cbr_decision else False
    )

    ab_result = ABTestResult(
        objective=request.action_plan.objective,
        cbr_decision=cbr_decision,
        cbr_confidence=cbr_confidence,
        framework_decision=framework_verdict.final_decision.value,
        framework_confidence=framework_verdict.confidence,
        decisions_match=decisions_match,
        timestamp=datetime.utcnow().isoformat(),
    )

    # Store result (keep last 100)
    ab_test_results.append(ab_result.model_dump())
    if len(ab_test_results) > 100:
        ab_test_results.pop(0)

    total_time_ms = (time.time() - start_time) * 1000

    return {
        "cbr": {
            "decision": cbr_decision,
            "confidence": cbr_confidence,
            "time_ms": cbr_time_ms,
            "used": cbr_decision is not None,
        },
        "frameworks": {
            "decision": framework_verdict.final_decision.value,
            "confidence": framework_verdict.confidence,
            "time_ms": framework_time_ms,
        },
        "comparison": {
            "decisions_match": decisions_match,
            "cbr_faster": cbr_time_ms < framework_time_ms if cbr_decision else False,
            "time_savings_ms": framework_time_ms - cbr_time_ms if cbr_decision else 0.0,
        },
        "total_time_ms": total_time_ms,
    }


@router.get("/ab-test/metrics", response_model=ABTestMetricsResponse)
async def get_ab_test_metrics() -> ABTestMetricsResponse:
    """Get A/B testing metrics."""
    if len(ab_test_results) == 0:
        return ABTestMetricsResponse(
            total_comparisons=0,
            agreement_rate=0.0,
            cbr_avg_confidence=0.0,
            framework_avg_confidence=0.0,
            cbr_faster_percentage=0.0,
            recent_results=[],
        )

    total = len(ab_test_results)
    matches = sum(1 for r in ab_test_results if r["decisions_match"])
    agreement_rate = (matches / total * 100) if total > 0 else 0.0

    cbr_confidences = [
        r["cbr_confidence"] for r in ab_test_results if r["cbr_confidence"] is not None
    ]
    cbr_avg = sum(cbr_confidences) / len(cbr_confidences) if cbr_confidences else 0.0

    framework_avg = sum(r["framework_confidence"] for r in ab_test_results) / total

    cbr_faster_percentage = 0.0

    recent = [ABTestResult(**r) for r in ab_test_results[-10:]]

    return ABTestMetricsResponse(
        total_comparisons=total,
        agreement_rate=agreement_rate,
        cbr_avg_confidence=cbr_avg,
        framework_avg_confidence=framework_avg,
        cbr_faster_percentage=cbr_faster_percentage,
        recent_results=recent,
    )
