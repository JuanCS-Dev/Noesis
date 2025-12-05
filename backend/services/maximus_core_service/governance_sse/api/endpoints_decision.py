"""
Decision Action Endpoints.

Endpoints for approving, rejecting, and escalating decisions.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from datetime import timedelta
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, status
from hitl import (
    ActionType,
    AutomationLevel,
    DecisionContext,
    DecisionQueue,
    DecisionStatus,
    HITLDecision,
    OperatorInterface,
    RiskLevel,
)

from ..event_broadcaster import EventBroadcaster
from ..sse_server import GovernanceSSEServer
from .models import (
    ApproveDecisionRequest,
    DecisionActionResponse,
    EscalateDecisionRequest,
    RejectDecisionRequest,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def create_decision_router(
    decision_queue: DecisionQueue,
    operator_interface: OperatorInterface,
    sse_server: GovernanceSSEServer,
    event_broadcaster: EventBroadcaster,
) -> APIRouter:
    """Create router for decision action endpoints."""
    router = APIRouter()

    @router.post("/decision/{decision_id}/approve", response_model=DecisionActionResponse)
    async def approve_decision(decision_id: str, request: ApproveDecisionRequest):
        """Approve a pending decision."""
        try:
            result = operator_interface.approve_decision(
                session_id=request.session_id,
                decision_id=decision_id,
                comment=request.comment or "",
            )

            await sse_server.notify_decision_resolved(
                decision_id=decision_id,
                status=DecisionStatus.APPROVED,
                operator_id=operator_interface.get_session(request.session_id).operator_id,
            )

            return DecisionActionResponse(
                decision_id=decision_id,
                action="approved",
                status=result.get("status", "approved"),
                message=f"Decision {decision_id} approved and executed",
                executed=result.get("executed"),
                result=result.get("result"),
                error=result.get("error"),
            )

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            logger.error(f"Approve failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Approval failed: {str(e)}",
            )

    @router.post("/decision/{decision_id}/reject", response_model=DecisionActionResponse)
    async def reject_decision(decision_id: str, request: RejectDecisionRequest):
        """Reject a pending decision."""
        try:
            result = operator_interface.reject_decision(
                session_id=request.session_id,
                decision_id=decision_id,
                reason=request.reason,
                comment=request.comment or "",
            )

            await sse_server.notify_decision_resolved(
                decision_id=decision_id,
                status=DecisionStatus.REJECTED,
                operator_id=operator_interface.get_session(request.session_id).operator_id,
            )

            return DecisionActionResponse(
                decision_id=decision_id,
                action="rejected",
                status="rejected",
                message=f"Decision {decision_id} rejected",
                executed=False,
            )

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            logger.error(f"Reject failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Rejection failed: {str(e)}",
            )

    @router.post("/decision/{decision_id}/escalate", response_model=DecisionActionResponse)
    async def escalate_decision(decision_id: str, request: EscalateDecisionRequest):
        """Escalate a pending decision to higher authority."""
        try:
            result = operator_interface.escalate_decision(
                session_id=request.session_id,
                decision_id=decision_id,
                reason=request.escalation_reason,
                comment=request.comment or "",
            )

            await sse_server.notify_decision_resolved(
                decision_id=decision_id,
                status=DecisionStatus.ESCALATED,
                operator_id=operator_interface.get_session(request.session_id).operator_id,
            )

            return DecisionActionResponse(
                decision_id=decision_id,
                action="escalated",
                status="escalated",
                message=f"Decision {decision_id} escalated",
                executed=False,
                result=result,
            )

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            logger.error(f"Escalate failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Escalation failed: {str(e)}",
            )

    @router.post("/test/enqueue")
    async def enqueue_test_decision(decision_dict: dict):
        """Enqueue a test decision (for E2E testing only).

        WARNING: This endpoint is for testing purposes only.
        In production, decisions are enqueued by MAXIMUS internally.
        """
        try:
            context_dict = decision_dict.get("context", {})
            context = DecisionContext(
                action_type=ActionType(context_dict.get("action_type", "block_ip")),
                action_params=context_dict.get("action_params", {}),
                ai_reasoning=context_dict.get("ai_reasoning", ""),
                confidence=context_dict.get("confidence", 0.0),
                threat_score=context_dict.get("threat_score", 0.0),
                threat_type=context_dict.get("threat_type", "unknown"),
                metadata=context_dict.get("metadata", {}),
            )

            decision = HITLDecision(
                decision_id=decision_dict.get(
                    "decision_id", f"test_{datetime.now(UTC).timestamp()}"
                ),
                context=context,
                risk_level=RiskLevel(decision_dict.get("risk_level", "high")),
                automation_level=AutomationLevel(
                    decision_dict.get("automation_level", "supervised")
                ),
                created_at=datetime.now(UTC),
                sla_deadline=datetime.now(UTC) + timedelta(minutes=10),
                status=DecisionStatus.PENDING,
            )

            decision_queue.enqueue(decision)

            await event_broadcaster.broadcast_decision_pending(decision)

            logger.info(f"Test decision enqueued: {decision.decision_id}")

            return {
                "status": "success",
                "decision_id": decision.decision_id,
                "risk_level": decision.risk_level.value,
                "message": "Test decision enqueued successfully",
            }

        except Exception as e:
            logger.error(f"Failed to enqueue test decision: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Enqueue failed: {str(e)}",
            )

    return router
