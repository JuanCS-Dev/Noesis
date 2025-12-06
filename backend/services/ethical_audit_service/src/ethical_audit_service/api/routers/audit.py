"""Ethical Decision Logging & Human Override Endpoints."""

from __future__ import annotations

import time
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from ethical_audit_service.auth import TokenData, require_auditor_or_admin, require_soc_or_admin
from ethical_audit_service.models import (
    ConsequentialistResult,
    DecisionHistoryQuery,
    DecisionHistoryResponse,
    DecisionType,
    EthicalDecisionLog,
    EthicalDecisionResponse,
    FinalDecision,
    HumanOverrideRequest,
    HumanOverrideResponse,
    KantianResult,
    PrinciplismResult,
    RiskLevel,
    VirtueEthicsResult,
)

from ..state import get_db, get_limiter

router = APIRouter(prefix="/audit", tags=["audit"])


@router.post("/decision", response_model=dict[str, Any])
async def log_decision(
    request: Request,
    decision_log: EthicalDecisionLog,
    current_user: TokenData = Depends(require_soc_or_admin),
) -> dict[str, Any]:
    """Log an ethical decision to the audit database."""
    limiter = get_limiter()
    await limiter.limit("100/minute")(request)

    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        decision_id = await db.log_decision(decision_log)

        return {
            "status": "success",
            "decision_id": str(decision_id),
            "timestamp": decision_log.timestamp.isoformat(),
            "message": "Ethical decision logged successfully",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log decision: {e!s}") from e


@router.get("/decision/{decision_id}", response_model=dict[str, Any])
async def get_decision(
    decision_id: uuid.UUID,
    current_user: TokenData = Depends(require_auditor_or_admin),
) -> dict[str, Any]:
    """Retrieve a specific ethical decision by ID."""
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    decision = await db.get_decision(decision_id)

    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    return decision


@router.post("/decisions/query", response_model=DecisionHistoryResponse)
async def query_decisions(
    request: Request,
    query: DecisionHistoryQuery,
    current_user: TokenData = Depends(require_auditor_or_admin),
) -> DecisionHistoryResponse:
    """Query ethical decisions with advanced filtering."""
    limiter = get_limiter()
    await limiter.limit("30/minute")(request)

    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    start_time = time.time()

    try:
        decisions, total_count = await db.query_decisions(query)

        query_time_ms = int((time.time() - start_time) * 1000)

        decision_responses = []
        for dec in decisions:
            kantian = KantianResult(**dec["kantian_result"]) if dec.get("kantian_result") else None
            consequentialist = (
                ConsequentialistResult(**dec["consequentialist_result"])
                if dec.get("consequentialist_result")
                else None
            )
            virtue = (
                VirtueEthicsResult(**dec["virtue_ethics_result"])
                if dec.get("virtue_ethics_result")
                else None
            )
            principi = (
                PrinciplismResult(**dec["principialism_result"])
                if dec.get("principialism_result")
                else None
            )

            decision_responses.append(
                EthicalDecisionResponse(
                    decision_id=dec["id"],
                    timestamp=dec["timestamp"],
                    decision_type=DecisionType(dec["decision_type"]),
                    action_description=dec["action_description"],
                    system_component=dec["system_component"],
                    kantian_result=kantian,
                    consequentialist_result=consequentialist,
                    virtue_ethics_result=virtue,
                    principialism_result=principi,
                    final_decision=FinalDecision(dec["final_decision"]),
                    final_confidence=dec["final_confidence"],
                    decision_explanation=dec["decision_explanation"],
                    total_latency_ms=dec["total_latency_ms"],
                    risk_level=RiskLevel(dec["risk_level"]),
                    automated=dec["automated"],
                )
            )

        return DecisionHistoryResponse(
            total_count=total_count,
            decisions=decision_responses,
            query_time_ms=query_time_ms,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {e!s}") from e


@router.post("/override", response_model=HumanOverrideResponse)
async def log_override(
    override: HumanOverrideRequest,
    current_user: TokenData = Depends(require_soc_or_admin),
) -> HumanOverrideResponse:
    """Log a human override of an AI ethical decision."""
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    decision = await db.get_decision(override.decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    try:
        override_id = await db.log_override(override)

        return HumanOverrideResponse(
            override_id=override_id,
            decision_id=override.decision_id,
            timestamp=datetime.utcnow(),
            operator_id=override.operator_id,
            operator_role=override.operator_role,
            override_decision=override.override_decision,
            justification=override.justification,
            override_reason=override.override_reason,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log override: {e!s}") from e


@router.get("/overrides/{decision_id}", response_model=list[dict[str, Any]])
async def get_overrides(decision_id: uuid.UUID) -> list[dict[str, Any]]:
    """Get all human overrides for a specific decision."""
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    overrides = await db.get_overrides_by_decision(decision_id)
    return overrides
