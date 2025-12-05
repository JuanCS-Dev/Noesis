"""HITL/HOTL Decision Endpoints."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.services.ethical_audit_service.auth import TokenData, require_auditor_or_admin, require_soc_or_admin

from ..state import get_app_state_value, set_app_state_value

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/hitl", tags=["hitl"])


def _init_hitl_framework() -> dict[str, Any]:
    """Initialize HITL framework if not exists."""
    if get_app_state_value("hitl_framework") is not None:
        return {
            "framework": get_app_state_value("hitl_framework"),
            "queue": get_app_state_value("hitl_queue"),
            "audit": get_app_state_value("hitl_audit"),
            "operator_interface": get_app_state_value("hitl_operator_interface"),
            "escalation": get_app_state_value("hitl_escalation"),
        }

    from maximus_core_service.hitl import (
        AuditTrail,
        DecisionQueue,
        EscalationManager,
        HITLConfig,
        HITLDecisionFramework,
        OperatorInterface,
    )

    config = HITLConfig()
    framework = HITLDecisionFramework(config=config)
    queue = DecisionQueue()
    audit = AuditTrail()
    escalation = EscalationManager()
    operator_interface = OperatorInterface(
        decision_framework=framework,
        decision_queue=queue,
        escalation_manager=escalation,
        audit_trail=audit,
    )

    framework.set_decision_queue(queue)
    framework.set_audit_trail(audit)

    set_app_state_value("hitl_framework", framework)
    set_app_state_value("hitl_queue", queue)
    set_app_state_value("hitl_audit", audit)
    set_app_state_value("hitl_operator_interface", operator_interface)
    set_app_state_value("hitl_escalation", escalation)

    logger.info("HITL framework initialized")

    return {
        "framework": framework,
        "queue": queue,
        "audit": audit,
        "operator_interface": operator_interface,
        "escalation": escalation,
    }


def _get_operator_session(current_user: TokenData, interface: Any) -> Any:
    """Get or create operator session."""
    sessions = get_app_state_value("hitl_operator_sessions")
    if sessions is None:
        sessions = {}
        set_app_state_value("hitl_operator_sessions", sessions)

    operator_id = current_user.username
    session_key = f"{operator_id}_{current_user.role}"

    if session_key not in sessions:
        session = interface.create_session(
            operator_id=operator_id,
            operator_name=current_user.username,
            operator_role=current_user.role,
        )
        sessions[session_key] = session
    else:
        session = sessions[session_key]

    return session


@router.post("/evaluate")
async def hitl_evaluate_decision(
    request: dict[str, Any],
    current_user: TokenData = Depends(require_soc_or_admin),
) -> dict[str, Any]:
    """Submit AI decision for HITL evaluation."""
    try:
        components = _init_hitl_framework()
        framework = components["framework"]

        action_type_str = request.get("action_type", "").upper()
        from maximus_core_service.hitl import ActionType

        try:
            action_type = ActionType[action_type_str]
        except KeyError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid action_type: {request.get('action_type')}"
            ) from e

        result = framework.evaluate_action(
            action_type=action_type,
            action_params=request.get("action_params", {}),
            ai_reasoning=request.get("ai_reasoning", ""),
            confidence=float(request.get("confidence", 0.0)),
            threat_score=float(request.get("threat_score", 0.0)),
            affected_assets=request.get("affected_assets", []),
            asset_criticality=request.get("asset_criticality", "medium"),
            business_impact=request.get("business_impact", ""),
            **request.get("metadata", {}),
        )

        response = {
            "decision_id": result.decision.decision_id,
            "automation_level": result.decision.automation_level.value,
            "risk_level": result.decision.risk_level.value,
            "status": result.decision.status.value,
            "executed": result.executed,
            "queued": result.queued,
            "rejected": result.rejected,
            "sla_deadline": (
                result.decision.sla_deadline.isoformat()
                if result.decision.sla_deadline
                else None
            ),
            "processing_time": result.processing_time,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if result.executed:
            response["result"] = result.execution_output
        if result.execution_error:
            response["error"] = result.execution_error

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("HITL evaluate failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/queue")
async def hitl_get_queue(
    risk_level: str | None = None,
    limit: int = 20,
    current_user: TokenData = Depends(require_soc_or_admin),
) -> dict[str, Any]:
    """Get pending decisions from HITL queue."""
    try:
        queue = get_app_state_value("hitl_queue")
        if not queue:
            return {
                "pending_decisions": [],
                "total_in_queue": 0,
                "queue_size_by_risk": {},
                "error": "HITL not initialized",
            }

        risk_filter = None
        if risk_level:
            from maximus_core_service.hitl import RiskLevel

            try:
                risk_filter = RiskLevel[risk_level.upper()]
            except KeyError as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid risk_level: {risk_level}"
                ) from e

        pending = queue.get_pending_decisions(risk_level=risk_filter)

        from maximus_core_service.hitl import RiskLevel

        pending.sort(
            key=lambda d: (
                4 - list(RiskLevel).index(d.risk_level),
                d.sla_deadline or datetime.max,
            )
        )
        pending = pending[:limit]

        decisions_data = []
        for decision in pending:
            time_remaining = decision.get_time_remaining()
            decisions_data.append(
                {
                    "decision_id": decision.decision_id,
                    "action_type": decision.context.action_type.value,
                    "action_params": decision.context.action_params,
                    "ai_reasoning": decision.context.ai_reasoning,
                    "confidence": decision.context.confidence,
                    "threat_score": decision.context.threat_score,
                    "risk_level": decision.risk_level.value,
                    "automation_level": decision.automation_level.value,
                    "created_at": decision.created_at.isoformat(),
                    "sla_deadline": (
                        decision.sla_deadline.isoformat() if decision.sla_deadline else None
                    ),
                    "time_remaining_seconds": (
                        int(time_remaining.total_seconds()) if time_remaining else None
                    ),
                }
            )

        queue_sizes = queue.get_size_by_risk()

        return {
            "pending_decisions": decisions_data,
            "total_in_queue": queue.get_total_size(),
            "queue_size_by_risk": {level.value: size for level, size in queue_sizes.items()},
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("HITL queue failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/approve")
async def hitl_approve_decision(
    request: dict[str, Any],
    current_user: TokenData = Depends(require_soc_or_admin),
) -> dict[str, Any]:
    """Approve and execute HITL decision."""
    try:
        interface = get_app_state_value("hitl_operator_interface")
        if not interface:
            raise HTTPException(status_code=503, detail="HITL not initialized")

        session = _get_operator_session(current_user, interface)

        decision_id = request.get("decision_id")
        if not decision_id:
            raise HTTPException(status_code=400, detail="decision_id required")

        comment = request.get("operator_comment", "")
        modifications = request.get("modifications")

        if modifications:
            result = interface.modify_and_approve(
                session_id=session.session_id,
                decision_id=decision_id,
                modifications=modifications,
                comment=comment,
            )
        else:
            result = interface.approve_decision(
                session_id=session.session_id,
                decision_id=decision_id,
                comment=comment,
            )

        return {
            **result,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("HITL approve failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/reject")
async def hitl_reject_decision(
    request: dict[str, Any],
    current_user: TokenData = Depends(require_soc_or_admin),
) -> dict[str, Any]:
    """Reject HITL decision."""
    try:
        interface = get_app_state_value("hitl_operator_interface")
        if not interface:
            raise HTTPException(status_code=503, detail="HITL not initialized")

        session = _get_operator_session(current_user, interface)

        decision_id = request.get("decision_id")
        reason = request.get("reason")

        if not decision_id or not reason:
            raise HTTPException(status_code=400, detail="decision_id and reason required")

        result = interface.reject_decision(
            session_id=session.session_id,
            decision_id=decision_id,
            reason=reason,
            comment=request.get("operator_comment", ""),
        )

        return {
            **result,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("HITL reject failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/escalate")
async def hitl_escalate_decision(
    request: dict[str, Any],
    current_user: TokenData = Depends(require_soc_or_admin),
) -> dict[str, Any]:
    """Escalate HITL decision to higher authority."""
    try:
        interface = get_app_state_value("hitl_operator_interface")
        if not interface:
            raise HTTPException(status_code=503, detail="HITL not initialized")

        session = _get_operator_session(current_user, interface)

        decision_id = request.get("decision_id")
        reason = request.get("reason")

        if not decision_id or not reason:
            raise HTTPException(status_code=400, detail="decision_id and reason required")

        result = interface.escalate_decision(
            session_id=session.session_id,
            decision_id=decision_id,
            reason=reason,
            comment=request.get("operator_comment", ""),
        )

        return {
            **result,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("HITL escalate failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/audit")
async def hitl_query_audit(
    decision_id: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    event_type: str | None = None,
    limit: int = 100,
    current_user: TokenData = Depends(require_auditor_or_admin),
) -> dict[str, Any]:
    """Query HITL audit trail."""
    try:
        audit = get_app_state_value("hitl_audit")
        if not audit:
            return {"audit_entries": [], "total_entries": 0, "error": "HITL not initialized"}

        from maximus_core_service.hitl import AuditQuery

        query_params: dict[str, Any] = {"limit": limit}

        if decision_id:
            query_params["decision_ids"] = [decision_id]

        if start_time:
            query_params["start_time"] = datetime.fromisoformat(
                start_time.replace("Z", "+00:00")
            )

        if end_time:
            query_params["end_time"] = datetime.fromisoformat(end_time.replace("Z", "+00:00"))

        if event_type:
            query_params["event_types"] = [event_type]

        query = AuditQuery(**query_params)

        entries = audit.query(query, redact_pii=True)

        entries_data = [
            {
                "entry_id": entry.entry_id,
                "decision_id": entry.decision_id,
                "event_type": entry.event_type,
                "event_description": entry.event_description,
                "actor_type": entry.actor_type,
                "actor_id": entry.actor_id,
                "timestamp": entry.timestamp.isoformat(),
                "decision_snapshot": entry.decision_snapshot,
                "context_snapshot": entry.context_snapshot,
                "compliance_tags": entry.compliance_tags,
            }
            for entry in entries
        ]

        return {
            "audit_entries": entries_data,
            "total_entries": len(entries),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.exception("HITL audit query failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e
