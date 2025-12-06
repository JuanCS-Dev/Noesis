"""HITL Backend - Decision Management Endpoints.

Endpoints for submitting, reviewing, and managing decisions.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from .auth import get_current_active_analyst, get_current_user
from .database import db
from .models import (
    ActionType,
    DecisionCreate,
    DecisionPriority,
    DecisionRequest,
    DecisionResponse,
    DecisionStats,
    DecisionStatus,
    UserInDB,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/decisions", tags=["decisions"])


@router.post("/submit", response_model=Dict[str, str])
async def submit_decision_request(
    decision: DecisionRequest,
    current_user: UserInDB = Depends(get_current_user),
) -> Dict[str, str]:
    """Submit new decision request (from CANDI)."""
    existing = db.get_decision(decision.analysis_id)
    if existing:
        raise HTTPException(status_code=400, detail="Decision already exists")

    db.add_decision(decision)

    db.audit(
        "DECISION_SUBMITTED",
        current_user.username,
        {
            "analysis_id": decision.analysis_id,
            "priority": decision.priority.value,
            "threat_level": decision.threat_level,
        },
    )

    logger.info(
        "Decision submitted: %s (priority: %s, threat: %s)",
        decision.analysis_id,
        decision.priority.value,
        decision.threat_level,
    )

    return {
        "message": "Decision request submitted successfully",
        "analysis_id": decision.analysis_id,
    }


@router.get("/pending", response_model=List[DecisionRequest])
async def get_pending_decisions(
    priority: Optional[DecisionPriority] = None,
    limit: int = Query(50, le=100),
    current_analyst: UserInDB = Depends(get_current_active_analyst),
) -> List[DecisionRequest]:
    """Get pending decisions."""
    pending = db.get_pending_decisions(priority)
    return pending[:limit]


@router.get("/{analysis_id}", response_model=DecisionRequest)
async def get_decision(
    analysis_id: str,
    current_user: UserInDB = Depends(get_current_user),
) -> DecisionRequest:
    """Get specific decision request."""
    decision = db.get_decision(analysis_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision


@router.post("/{analysis_id}/decide", response_model=DecisionResponse)
async def make_decision(
    analysis_id: str,
    decision_data: DecisionCreate,
    current_analyst: UserInDB = Depends(get_current_active_analyst),
) -> DecisionResponse:
    """Make decision on request."""
    request = db.get_decision(analysis_id)
    if not request:
        raise HTTPException(status_code=404, detail="Decision request not found")

    if analysis_id in db.responses:
        raise HTTPException(status_code=400, detail="Decision already made")

    if decision_data.status == DecisionStatus.ESCALATED:
        if not decision_data.escalation_reason:
            raise HTTPException(status_code=400, detail="Escalation reason required")

    response = DecisionResponse(
        decision_id=analysis_id,
        status=decision_data.status,
        approved_actions=decision_data.approved_actions,
        notes=decision_data.notes,
        decided_by=current_analyst.username,
        decided_at=datetime.now(),
        escalation_reason=decision_data.escalation_reason,
    )

    db.add_response(response)

    db.audit(
        "DECISION_MADE",
        current_analyst.username,
        {
            "analysis_id": analysis_id,
            "status": decision_data.status.value,
            "actions": [a.value for a in decision_data.approved_actions],
        },
    )

    logger.info(
        "Decision made on %s by %s: %s",
        analysis_id,
        current_analyst.username,
        decision_data.status.value,
    )

    return response


@router.get("/{analysis_id}/response", response_model=DecisionResponse)
async def get_decision_response(
    analysis_id: str,
    current_user: UserInDB = Depends(get_current_user),
) -> DecisionResponse:
    """Get decision response."""
    response = db.responses.get(analysis_id)
    if not response:
        raise HTTPException(status_code=404, detail="Decision response not found")
    return response


@router.get("/stats/summary", response_model=DecisionStats)
async def get_decision_stats(
    current_user: UserInDB = Depends(get_current_user),
) -> DecisionStats:
    """Get decision statistics."""
    pending = db.get_pending_decisions()

    critical = len([d for d in pending if d.priority == DecisionPriority.CRITICAL])
    high = len([d for d in pending if d.priority == DecisionPriority.HIGH])
    medium = len([d for d in pending if d.priority == DecisionPriority.MEDIUM])
    low = len([d for d in pending if d.priority == DecisionPriority.LOW])

    completed = db.responses.values()
    if completed:
        response_times = []
        for response in completed:
            request = db.get_decision(response.decision_id)
            if request:
                delta = (response.decided_at - request.created_at).total_seconds() / 60
                response_times.append(delta)

        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
    else:
        avg_response_time = 0.0

    cutoff = datetime.now() - timedelta(hours=24)
    recent = len([d for d in db.decisions.values() if d.created_at > cutoff])

    return DecisionStats(
        total_pending=len(pending),
        critical_pending=critical,
        high_pending=high,
        medium_pending=medium,
        low_pending=low,
        total_completed=len(db.responses),
        avg_response_time_minutes=avg_response_time,
        decisions_last_24h=recent,
    )


@router.post("/{analysis_id}/escalate", response_model=DecisionResponse)
async def escalate_decision(
    analysis_id: str,
    escalation_reason: str,
    current_analyst: UserInDB = Depends(get_current_active_analyst),
) -> DecisionResponse:
    """Escalate decision to higher authority."""
    request = db.get_decision(analysis_id)
    if not request:
        raise HTTPException(status_code=404, detail="Decision not found")

    response = DecisionResponse(
        decision_id=analysis_id,
        status=DecisionStatus.ESCALATED,
        approved_actions=[],
        notes=f"Escalated by {current_analyst.username}",
        decided_by=current_analyst.username,
        decided_at=datetime.now(),
        escalation_reason=escalation_reason,
    )

    db.add_response(response)

    db.audit(
        "DECISION_ESCALATED",
        current_analyst.username,
        {"analysis_id": analysis_id, "reason": escalation_reason},
    )

    logger.warning("Decision escalated: %s - %s", analysis_id, escalation_reason)

    return response
