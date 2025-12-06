"""HITL Engine - Main Engine Class.

Human-In-The-Loop engine combining alert and decision management.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from .alerts import AlertManagementMixin
from .decisions import DecisionManagementMixin
from .models import (
    Alert,
    AlertStatus,
    AuditLog,
    DecisionRequest,
    DecisionResponse,
    HITLConfig,
    WorkflowState,
)


class HITLEngine(AlertManagementMixin, DecisionManagementMixin):
    """Human-In-The-Loop engine for managing alerts and decisions."""

    def __init__(self, config: HITLConfig | None = None) -> None:
        """Initialize HITL engine."""
        self.config = config or HITLConfig()
        self.alerts: Dict[str, Alert] = {}
        self.decision_requests: Dict[str, DecisionRequest] = {}
        self.decision_responses: Dict[str, DecisionResponse] = {}
        self.audit_logs: List[AuditLog] = []
        self.workflows: Dict[str, WorkflowState] = {}

        # Tracking
        self.alerts_by_status: Dict[AlertStatus, Set[str]] = defaultdict(set)
        self.alerts_by_priority: Dict[str, Set[str]] = defaultdict(set)
        self.pending_decisions: Set[str] = set()

        # Metrics
        self.total_alerts = 0
        self.total_decisions = 0
        self.escalation_count = 0

        # Running state
        self._running = False
        self._cleanup_task = None

    async def get_alert_timeline(self, alert_id: str) -> List[Dict[str, Any]]:
        """Get timeline of events for an alert."""
        if alert_id not in self.alerts:
            return []

        timeline = []
        alert = self.alerts[alert_id]

        timeline.append(
            {
                "timestamp": alert.created_at,
                "event": "alert_created",
                "details": {
                    "title": alert.title,
                    "priority": alert.priority.value,
                    "threat_score": alert.threat_score,
                },
            }
        )

        if alert.acknowledged_at:
            timeline.append(
                {
                    "timestamp": alert.acknowledged_at,
                    "event": "alert_acknowledged",
                    "details": {"assigned_to": alert.assigned_to},
                }
            )

        for request in self.decision_requests.values():
            if request.alert_id == alert_id:
                timeline.append(
                    {
                        "timestamp": request.created_at,
                        "event": "decision_requested",
                        "details": {
                            "type": request.decision_type.value,
                            "target": request.target,
                        },
                    }
                )

        for response in self.decision_responses.values():
            if response.alert_id == alert_id:
                timeline.append(
                    {
                        "timestamp": response.created_at,
                        "event": f"decision_{response.status.value}",
                        "details": {
                            "type": response.decision_type.value,
                            "approver": response.approver,
                        },
                    }
                )

        if alert.resolved_at:
            timeline.append(
                {
                    "timestamp": alert.resolved_at,
                    "event": "alert_resolved",
                    "details": {"status": alert.status.value},
                }
            )

        timeline.sort(key=lambda x: x["timestamp"])

        return timeline

    async def get_audit_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        actor: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Get audit logs with optional filters."""
        logs = self.audit_logs

        if start_time:
            logs = [log for log in logs if log.timestamp >= start_time]

        if end_time:
            logs = [log for log in logs if log.timestamp <= end_time]

        if actor:
            logs = [log for log in logs if log.actor == actor]

        if action:
            logs = [log for log in logs if log.action == action]

        logs.sort(key=lambda x: x.timestamp, reverse=True)

        return logs[:limit]

    async def _cleanup_old_alerts(self) -> None:
        """Clean up old resolved alerts."""
        cutoff = datetime.utcnow() - timedelta(days=self.config.alert_retention_days)

        to_remove = []
        for alert_id, alert in self.alerts.items():
            if alert.status == AlertStatus.RESOLVED and alert.resolved_at:
                if alert.resolved_at < cutoff:
                    to_remove.append(alert_id)

        for alert_id in to_remove:
            alert = self.alerts.pop(alert_id)
            self.alerts_by_status[alert.status].discard(alert_id)
            self.alerts_by_priority[alert.priority].discard(alert_id)

    async def _audit_log(
        self,
        action: str,
        actor: str,
        target: Dict[str, Any],
        result: str,
        details: Dict[str, Any] | None = None,
    ) -> None:
        """Create an audit log entry."""
        if not self.config.audit_all_actions:
            return

        log = AuditLog(
            action=action,
            actor=actor,
            target=target,
            result=result,
            details=details or {},
        )

        self.audit_logs.append(log)

        if len(self.audit_logs) > 10000:
            self.audit_logs = self.audit_logs[-5000:]

    async def start(self) -> None:
        """Start HITL engine."""
        self._running = True

        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

        await self._audit_log(
            action="engine_started",
            actor="system",
            target={},
            result="success",
            details={},
        )

    async def stop(self) -> None:
        """Stop HITL engine."""
        self._running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        await self._audit_log(
            action="engine_stopped",
            actor="system",
            target={},
            result="success",
            details={
                "total_alerts": self.total_alerts,
                "total_decisions": self.total_decisions,
            },
        )

    async def _periodic_cleanup(self) -> None:
        """Periodic cleanup of old data."""
        while self._running:
            try:
                await asyncio.sleep(3600)
                await self._cleanup_old_alerts()

                now = datetime.utcnow()
                for alert_id in list(self.alerts_by_status[AlertStatus.PENDING]):
                    if alert_id in self.alerts:
                        alert = self.alerts[alert_id]
                        age_minutes = (now - alert.created_at).total_seconds() / 60

                        if age_minutes > self.config.auto_escalate_after_minutes:
                            await self._auto_escalate(alert)

            except asyncio.CancelledError:
                break
            except Exception:
                pass

    def get_metrics(self) -> Dict[str, Any]:
        """Get HITL metrics."""
        return {
            "running": self._running,
            "total_alerts": self.total_alerts,
            "active_alerts": len(self.alerts),
            "pending_alerts": len(self.alerts_by_status[AlertStatus.PENDING]),
            "acknowledged_alerts": len(self.alerts_by_status[AlertStatus.ACKNOWLEDGED]),
            "resolved_alerts": len(self.alerts_by_status[AlertStatus.RESOLVED]),
            "escalated_alerts": len(self.alerts_by_status[AlertStatus.ESCALATED]),
            "total_decisions": self.total_decisions,
            "pending_decisions": len(self.pending_decisions),
            "escalation_count": self.escalation_count,
            "audit_logs": len(self.audit_logs),
            "active_workflows": len(self.workflows),
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"HITLEngine(running={self._running}, "
            f"alerts={len(self.alerts)}, "
            f"pending_decisions={len(self.pending_decisions)}, "
            f"audit_logs={len(self.audit_logs)})"
        )
