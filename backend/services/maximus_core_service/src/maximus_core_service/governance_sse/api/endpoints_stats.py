"""
Health and Stats Endpoints.

Endpoints for health checks and pending decision statistics.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, status
from maximus_core_service.hitl import DecisionQueue, DecisionStatus, OperatorInterface, RiskLevel

from ..sse_server import GovernanceSSEServer
from .models import (
    DecisionResponse,
    HealthResponse,
    OperatorStatsResponse,
    PendingStatsResponse,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def create_stats_router(
    decision_queue: DecisionQueue,
    operator_interface: OperatorInterface,
    sse_server: GovernanceSSEServer,
) -> APIRouter:
    """Create router for health and stats endpoints."""
    router = APIRouter()

    @router.get("/health", response_model=HealthResponse)
    async def get_health():
        """Get server health status."""
        health = sse_server.get_health()
        return HealthResponse(**health)

    @router.get("/pending", response_model=PendingStatsResponse)
    async def get_pending_stats():
        """Get statistics about pending decisions."""
        pending = decision_queue.get_pending_decisions()

        total = len(pending)
        by_risk = {level.value: 0 for level in RiskLevel}

        oldest_pending_seconds = None
        if pending:
            for decision in pending:
                by_risk[decision.risk_level.value] += 1

            oldest = min(pending, key=lambda d: d.created_at)
            age = (datetime.now(UTC) - oldest.created_at).total_seconds()
            oldest_pending_seconds = int(age)

        sla_violations = sum(
            1 for d in pending if d.sla_deadline and datetime.now(UTC) > d.sla_deadline
        )

        return PendingStatsResponse(
            total_pending=total,
            by_risk_level=by_risk,
            oldest_pending_seconds=oldest_pending_seconds,
            sla_violations=sla_violations,
        )

    @router.get("/decision/{decision_id}", response_model=DecisionResponse)
    async def get_decision(decision_id: str):
        """Get a specific decision by ID."""
        try:
            decision = decision_queue.get_decision(decision_id)

            if decision is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Decision {decision_id} not found",
                )

            context_dict = {
                "action_type": decision.context.action_type.value,
                "action_params": decision.context.action_params,
                "ai_reasoning": decision.context.ai_reasoning,
                "confidence": decision.context.confidence,
                "threat_score": decision.context.threat_score,
                "threat_type": decision.context.threat_type,
                "metadata": decision.context.metadata,
            }

            resolution = None
            if decision.status != DecisionStatus.PENDING:
                resolution = {
                    "status": decision.status.value,
                    "resolved_at": (
                        decision.resolved_at.isoformat()
                        if decision.resolved_at
                        else None
                    ),
                    "resolved_by": decision.resolved_by,
                }

            return DecisionResponse(
                decision_id=decision.decision_id,
                status=decision.status.value,
                risk_level=decision.risk_level.value,
                automation_level=decision.automation_level.value,
                created_at=decision.created_at.isoformat(),
                sla_deadline=(
                    decision.sla_deadline.isoformat() if decision.sla_deadline else None
                ),
                context=context_dict,
                resolution=resolution,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get decision {decision_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve decision: {str(e)}",
            )

    @router.get("/session/{operator_id}/stats", response_model=OperatorStatsResponse)
    async def get_operator_stats(operator_id: str):
        """Get operator statistics."""
        metrics = operator_interface._operator_metrics.get(operator_id)

        active_sessions = [
            session
            for session in operator_interface._sessions.values()
            if session.operator_id == operator_id
        ]

        if metrics is None and not active_sessions:
            return OperatorStatsResponse(
                operator_id=operator_id,
                total_sessions=0,
                total_decisions_reviewed=0,
                total_approved=0,
                total_rejected=0,
                total_escalated=0,
                approval_rate=0.0,
                rejection_rate=0.0,
                escalation_rate=0.0,
                average_review_time=0.0,
            )

        total_sessions = metrics.total_sessions if metrics else 0
        total_sessions += len(active_sessions)

        total_reviewed = metrics.total_decisions_reviewed if metrics else 0
        total_approved = metrics.total_approved if metrics else 0
        total_rejected = metrics.total_rejected if metrics else 0
        total_escalated = metrics.total_escalated if metrics else 0

        for session in active_sessions:
            total_reviewed += session.decisions_reviewed
            total_approved += session.decisions_approved
            total_rejected += session.decisions_rejected
            total_escalated += session.decisions_escalated

        approval_rate = total_approved / total_reviewed if total_reviewed > 0 else 0.0
        rejection_rate = total_rejected / total_reviewed if total_reviewed > 0 else 0.0
        escalation_rate = (
            total_escalated / total_reviewed if total_reviewed > 0 else 0.0
        )

        avg_review_time = metrics.average_review_time if metrics else 0.0

        return OperatorStatsResponse(
            operator_id=operator_id,
            total_sessions=total_sessions,
            total_decisions_reviewed=total_reviewed,
            total_approved=total_approved,
            total_rejected=total_rejected,
            total_escalated=total_escalated,
            approval_rate=approval_rate,
            rejection_rate=rejection_rate,
            escalation_rate=escalation_rate,
            average_review_time=avg_review_time,
        )

    return router
