"""HITL Engine - Decision Management Mixin.

Handles decision requests, approvals, and rejections.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List

from .models import (
    ApprovalStatus,
    DecisionRequest,
    DecisionResponse,
    DecisionType,
    WorkflowState,
)


class DecisionManagementMixin:
    """Mixin for decision management operations."""

    async def request_decision(
        self,
        alert_id: str,
        decision_type: DecisionType,
        target: Dict[str, object],
        reason: str,
        risk_level: str = "medium",
    ) -> DecisionRequest:
        """Request a decision for an alert."""
        if alert_id not in self.alerts:
            raise ValueError(f"Alert {alert_id} not found")

        request = DecisionRequest(
            alert_id=alert_id,
            decision_type=decision_type,
            target=target,
            reason=reason,
            risk_level=risk_level,
            expires_at=datetime.utcnow()
            + timedelta(minutes=self.config.decision_timeout_minutes),
        )

        self.decision_requests[request.request_id] = request
        self.pending_decisions.add(request.request_id)
        self.total_decisions += 1

        if alert_id not in self.workflows:
            workflow = WorkflowState(alert_id=alert_id, current_stage="decision_pending")
            self.workflows[alert_id] = workflow

        self.workflows[alert_id].decisions_pending.append(request.request_id)

        await self._audit_log(
            action="decision_requested",
            actor="system",
            target={"request_id": request.request_id, "alert_id": alert_id},
            result="success",
            details={
                "decision_type": decision_type.value,
                "target": target,
                "reason": reason,
            },
        )

        return request

    async def approve_decision(
        self,
        request_id: str,
        approver: str,
        notes: str | None = None,
    ) -> DecisionResponse:
        """Approve a decision request."""
        if request_id not in self.decision_requests:
            raise ValueError(f"Request {request_id} not found")

        request = self.decision_requests[request_id]

        if request.expires_at and datetime.utcnow() > request.expires_at:
            response = DecisionResponse(
                request_id=request_id,
                alert_id=request.alert_id,
                decision_type=request.decision_type,
                status=ApprovalStatus.EXPIRED,
            )
        else:
            response = DecisionResponse(
                request_id=request_id,
                alert_id=request.alert_id,
                decision_type=request.decision_type,
                status=ApprovalStatus.APPROVED,
                approver=approver,
                approved_at=datetime.utcnow(),
            )

            response.execution_result = {
                "phase": "1",
                "action": "logged_only",
                "would_execute": request.decision_type.value,
                "target": request.target,
            }

        self.decision_responses[response.response_id] = response
        self.pending_decisions.discard(request_id)

        if request.alert_id in self.workflows:
            workflow = self.workflows[request.alert_id]
            workflow.decisions_pending.remove(request_id)
            workflow.stages_completed.append(f"decision_{request.decision_type.value}")
            workflow.updated_at = datetime.utcnow()

        if request.alert_id in self.alerts and notes:
            self.alerts[request.alert_id].notes.append(
                f"[{approver}] Approved: {request.decision_type.value} - {notes}"
            )

        await self._audit_log(
            action="decision_approved",
            actor=approver,
            target={"request_id": request_id, "alert_id": request.alert_id},
            result="success",
            details={"decision_type": request.decision_type.value, "notes": notes},
        )

        return response

    async def reject_decision(
        self,
        request_id: str,
        rejector: str,
        reason: str,
    ) -> DecisionResponse:
        """Reject a decision request."""
        if request_id not in self.decision_requests:
            raise ValueError(f"Request {request_id} not found")

        request = self.decision_requests[request_id]

        response = DecisionResponse(
            request_id=request_id,
            alert_id=request.alert_id,
            decision_type=request.decision_type,
            status=ApprovalStatus.REJECTED,
            approver=rejector,
            rejection_reason=reason,
        )

        self.decision_responses[response.response_id] = response
        self.pending_decisions.discard(request_id)

        if request.alert_id in self.workflows:
            workflow = self.workflows[request.alert_id]
            workflow.decisions_pending.remove(request_id)
            workflow.updated_at = datetime.utcnow()

        if request.alert_id in self.alerts:
            self.alerts[request.alert_id].notes.append(
                f"[{rejector}] Rejected: {request.decision_type.value} - {reason}"
            )

        await self._audit_log(
            action="decision_rejected",
            actor=rejector,
            target={"request_id": request_id, "alert_id": request.alert_id},
            result="success",
            details={"decision_type": request.decision_type.value, "reason": reason},
        )

        return response

    async def get_pending_decisions(self) -> List[DecisionRequest]:
        """Get pending decision requests."""
        requests = []
        expired_requests = []

        for request_id in list(self.pending_decisions):
            if request_id in self.decision_requests:
                request = self.decision_requests[request_id]

                if request.expires_at and datetime.utcnow() > request.expires_at:
                    expired_requests.append(request_id)
                else:
                    requests.append(request)

        for request_id in expired_requests:
            self.pending_decisions.discard(request_id)
            request = self.decision_requests[request_id]

            response = DecisionResponse(
                request_id=request_id,
                alert_id=request.alert_id,
                decision_type=request.decision_type,
                status=ApprovalStatus.EXPIRED,
            )
            self.decision_responses[response.response_id] = response

        return requests
