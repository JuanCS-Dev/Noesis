"""
Core MIP Endpoints.

Main evaluation, health, frameworks, and metrics endpoints.

Author: Juan Carlos de Souza
Date: 2025-10-06
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status

from justice.precedent_database import CasePrecedent
from motor_integridade_processual.models.verdict import (
    DecisionLevel,
    EthicalVerdict,
    FrameworkName,
    FrameworkVerdict,
)

from .models import (
    EvaluationRequest,
    EvaluationResponse,
    FrameworkInfo,
    HealthResponse,
    MetricsResponse,
)
from .state import (
    cbr_engine,
    cbr_validators,
    evaluation_count,
    evaluation_times,
    decision_counts,
    frameworks,
    resolver,
    update_cbr_metrics,
    update_metrics,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=dict[str, str])
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "service": "Motor de Integridade Processual (MIP)",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        frameworks_loaded=len(frameworks),
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/frameworks", response_model=list[FrameworkInfo])
async def list_frameworks() -> list[FrameworkInfo]:
    """List available ethical frameworks."""
    framework_infos = []

    for name, framework in frameworks.items():
        framework_infos.append(
            FrameworkInfo(
                name=name.value,
                description=framework.__class__.__doc__ or "Ethical framework",
                weight=resolver.weights.get(name.value, 0.25),
                can_veto=name == FrameworkName.KANTIAN,
            )
        )

    return framework_infos


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    """Get evaluation metrics."""
    avg_time = (
        sum(evaluation_times) / len(evaluation_times) if evaluation_times else 0.0
    )

    return MetricsResponse(
        total_evaluations=evaluation_count,
        avg_evaluation_time_ms=avg_time,
        decision_breakdown=decision_counts,
    )


@router.post(
    "/evaluate", response_model=EvaluationResponse, status_code=status.HTTP_200_OK
)
async def evaluate_action_plan(request: EvaluationRequest) -> EvaluationResponse:
    """Evaluate an action plan against ethical frameworks with precedent-based reasoning."""
    start_time = time.time()

    try:
        logger.info(f"Evaluating action plan: {request.action_plan.objective}")

        # === PHASE 1: Try CBR (Precedent-Based Reasoning) ===
        cbr_result = None
        case_dict: dict[str, Any] = {}

        if cbr_engine is not None:
            try:
                case_dict = {
                    "objective": request.action_plan.objective,
                    "action_type": getattr(
                        request.action_plan, "action_type", "unknown"
                    ),
                    "context": getattr(request.action_plan, "context", {}),
                    "target": getattr(request.action_plan, "target", None),
                }

                cbr_result = await cbr_engine.full_cycle(
                    case_dict, validators=cbr_validators
                )

                if cbr_result and cbr_result.confidence > 0.8:
                    logger.info(
                        f"High-confidence precedent found "
                        f"(conf={cbr_result.confidence:.2f}), using directly"
                    )
                    update_cbr_metrics(precedent_used=True, shortcut=True)

                    decision_map = {
                        "approve": DecisionLevel.APPROVE,
                        "approve_with_monitoring": DecisionLevel.APPROVE_WITH_CONDITIONS,
                        "escalate": DecisionLevel.ESCALATE_TO_HITL,
                        "reject": DecisionLevel.REJECT,
                    }
                    decision = decision_map.get(
                        cbr_result.suggested_action, DecisionLevel.ESCALATE_TO_HITL
                    )

                    cbr_framework_verdict = FrameworkVerdict(
                        framework_name=FrameworkName.PRINCIPIALISM,
                        decision=decision,
                        confidence=cbr_result.confidence,
                        reasoning=f"Precedent-based decision: {cbr_result.rationale}",
                        rejection_reasons=[],
                        conditions=[],
                        metadata={
                            "source": "CBR",
                            "precedent_id": cbr_result.precedent_id,
                        },
                    )

                    final_verdict = EthicalVerdict(
                        action_plan_id=request.action_plan.id
                        or "00000000-0000-0000-0000-000000000000",
                        final_decision=decision,
                        confidence=cbr_result.confidence,
                        primary_reasons=[cbr_result.rationale],
                        framework_verdicts={
                            FrameworkName.PRINCIPIALISM: cbr_framework_verdict
                        },
                        resolution_method="CBR_PRECEDENT",
                        processing_time_ms=0.0,
                        metadata={
                            "minority_opinions": [],
                            "recommendations": [
                                f"Based on precedent #{cbr_result.precedent_id}"
                            ],
                        },
                    )

                elif cbr_result:
                    logger.info(
                        f"Low-confidence precedent found "
                        f"(conf={cbr_result.confidence:.2f}), falling back to frameworks"
                    )
                    update_cbr_metrics(precedent_used=True, shortcut=False)
                else:
                    logger.info("No applicable precedent found, using frameworks")

            except Exception as e:
                logger.warning(f"CBR cycle failed: {e}, falling back to frameworks")
                cbr_result = None

        # === PHASE 2: Framework Evaluation ===
        if cbr_result is None or cbr_result.confidence <= 0.8:
            framework_verdicts = []
            for name, framework in frameworks.items():
                try:
                    verdict = framework.evaluate(request.action_plan)
                    framework_verdicts.append(verdict)
                    logger.debug(
                        f"{name.value}: {verdict.decision.value} (score: {verdict.score})"
                    )
                except Exception as e:
                    logger.error(f"Framework {name.value} evaluation failed: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Framework evaluation failed: {str(e)}",
                    )

            try:
                final_verdict = resolver.resolve(
                    framework_verdicts, request.action_plan
                )
                logger.info(f"Final decision: {final_verdict.final_decision.value}")
            except Exception as e:
                logger.error(f"Conflict resolution failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Conflict resolution failed: {str(e)}",
                )

        elapsed_time = (time.time() - start_time) * 1000
        update_metrics(elapsed_time, final_verdict.final_decision.value)
        final_verdict.processing_time_ms = elapsed_time

        # === PHASE 3: Retain (Store as new precedent) ===
        if cbr_engine is not None:
            try:
                action_map = {
                    DecisionLevel.APPROVE: "approve",
                    DecisionLevel.APPROVE_WITH_CONDITIONS: "approve_with_monitoring",
                    DecisionLevel.ESCALATE_TO_HITL: "escalate",
                    DecisionLevel.REJECT: "reject",
                }
                action_taken = action_map.get(
                    final_verdict.final_decision, "unknown"
                )

                new_precedent = CasePrecedent(
                    situation=case_dict
                    if case_dict
                    else {
                        "objective": request.action_plan.objective,
                        "action_type": getattr(
                            request.action_plan, "action_type", "unknown"
                        ),
                        "context": getattr(request.action_plan, "context", {}),
                    },
                    action_taken=action_taken,
                    rationale=final_verdict.primary_reasons[0]
                    if final_verdict.primary_reasons
                    else "No rationale",
                    outcome=None,
                    success=None,
                    ethical_frameworks=[
                        fv.framework_name
                        for fv in final_verdict.framework_verdicts.values()
                    ],
                    constitutional_compliance={},
                    embedding=None,
                )

                await cbr_engine.retain(new_precedent)
                logger.info(f"Decision stored as precedent (action={action_taken})")

            except Exception as e:
                logger.warning(f"Failed to store precedent: {e}")

        return EvaluationResponse(verdict=final_verdict, evaluation_time_ms=elapsed_time)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during evaluation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}",
        )
