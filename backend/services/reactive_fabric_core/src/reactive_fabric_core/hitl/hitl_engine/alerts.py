"""HITL Engine - Alert Management Mixin.

Handles alert creation, acknowledgment, and status updates.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .models import (
    Alert,
    AlertPriority,
    AlertStatus,
    DecisionType,
)


class AlertManagementMixin:
    """Mixin for alert management operations."""

    async def create_alert(
        self,
        title: str,
        description: str,
        source: str,
        priority: AlertPriority,
        threat_score: float,
        entities: Dict[str, Any] | None = None,
        evidence: List[Dict[str, Any]] | None = None,
        mitre_tactics: List[str] | None = None,
        mitre_techniques: List[str] | None = None,
    ) -> Alert:
        """Create a new alert."""
        if len(self.alerts) >= self.config.max_pending_alerts:
            await self._cleanup_old_alerts()

        alert = Alert(
            title=title,
            description=description,
            source=source,
            priority=priority,
            threat_score=threat_score,
            entities=entities or {},
            evidence=evidence or [],
            mitre_tactics=mitre_tactics or [],
            mitre_techniques=mitre_techniques or [],
        )

        alert.recommended_actions = self._determine_recommended_actions(
            priority, threat_score, entities
        )

        related = await self._find_related_alerts(alert)
        if related:
            alert.related_alerts = [
                r.alert_id for r in related[: self.config.max_related_alerts]
            ]

        self.alerts[alert.alert_id] = alert
        self.alerts_by_status[alert.status].add(alert.alert_id)
        self.alerts_by_priority[alert.priority].add(alert.alert_id)

        self.total_alerts += 1

        if threat_score >= self.config.escalation_threshold:
            await self._auto_escalate(alert)

        await self._audit_log(
            action="alert_created",
            actor="system",
            target={"alert_id": alert.alert_id},
            result="success",
            details={"title": title, "priority": priority.value},
        )

        return alert

    async def acknowledge_alert(
        self,
        alert_id: str,
        assigned_to: str,
        notes: str | None = None,
    ) -> bool:
        """Acknowledge an alert."""
        if alert_id not in self.alerts:
            return False

        alert = self.alerts[alert_id]

        self.alerts_by_status[alert.status].discard(alert_id)
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        alert.assigned_to = assigned_to
        self.alerts_by_status[alert.status].add(alert_id)

        if notes:
            alert.notes.append(f"[{assigned_to}] {notes}")

        await self._audit_log(
            action="alert_acknowledged",
            actor=assigned_to,
            target={"alert_id": alert_id},
            result="success",
            details={"notes": notes},
        )

        return True

    async def update_alert_status(
        self,
        alert_id: str,
        status: AlertStatus,
        actor: str,
        notes: str | None = None,
    ) -> bool:
        """Update alert status."""
        if alert_id not in self.alerts:
            return False

        alert = self.alerts[alert_id]
        old_status = alert.status

        self.alerts_by_status[old_status].discard(alert_id)
        alert.status = status
        self.alerts_by_status[status].add(alert_id)

        if status == AlertStatus.RESOLVED:
            alert.resolved_at = datetime.utcnow()

        if notes:
            alert.notes.append(f"[{actor}] {notes}")

        await self._audit_log(
            action="alert_status_changed",
            actor=actor,
            target={"alert_id": alert_id},
            result="success",
            details={
                "old_status": old_status.value,
                "new_status": status.value,
                "notes": notes,
            },
        )

        return True

    async def get_pending_alerts(
        self,
        priority: Optional[AlertPriority] = None,
        limit: int = 100,
    ) -> List[Alert]:
        """Get pending alerts."""
        pending_ids = self.alerts_by_status[AlertStatus.PENDING]

        if priority:
            priority_ids = self.alerts_by_priority[priority]
            alert_ids = pending_ids.intersection(priority_ids)
        else:
            alert_ids = pending_ids

        alerts = [self.alerts[aid] for aid in alert_ids if aid in self.alerts]

        priority_order = {
            AlertPriority.CRITICAL: 0,
            AlertPriority.HIGH: 1,
            AlertPriority.MEDIUM: 2,
            AlertPriority.LOW: 3,
            AlertPriority.INFO: 4,
        }

        alerts.sort(key=lambda a: (priority_order[a.priority], a.created_at))

        return alerts[:limit]

    def _determine_recommended_actions(
        self,
        priority: AlertPriority,
        threat_score: float,
        entities: Dict[str, Any] | None,
    ) -> List[DecisionType]:
        """Determine recommended actions based on alert details."""
        actions = [DecisionType.INVESTIGATE]

        if entities is None:
            entities = {}

        if priority == AlertPriority.CRITICAL or threat_score >= 0.8:
            if "ip" in entities:
                actions.append(DecisionType.BLOCK_IP)
            if "hostname" in entities:
                actions.append(DecisionType.ISOLATE_HOST)
            if "process" in entities:
                actions.append(DecisionType.TERMINATE_PROCESS)
            if "user" in entities:
                actions.append(DecisionType.REVOKE_ACCESS)
            actions.append(DecisionType.ESCALATE)

        elif priority == AlertPriority.HIGH or threat_score >= 0.6:
            if "ip" in entities:
                actions.append(DecisionType.BLOCK_IP)
            if "file_hash" in entities:
                actions.append(DecisionType.QUARANTINE_FILE)

        return actions

    async def _find_related_alerts(self, alert: Alert) -> List[Alert]:
        """Find alerts related to the given alert."""
        related = []

        window_start = alert.created_at - timedelta(
            minutes=self.config.alert_grouping_window_minutes
        )

        for other_id, other in self.alerts.items():
            if other_id == alert.alert_id:
                continue

            if other.created_at < window_start:
                continue

            common_entities = set(alert.entities.keys()) & set(other.entities.keys())
            if common_entities:
                for key in common_entities:
                    if alert.entities[key] == other.entities[key]:
                        related.append(other)
                        break
            elif alert.source == other.source:
                related.append(other)

        return related

    async def _auto_escalate(self, alert: Alert) -> None:
        """Auto-escalate high-threat alerts."""
        self.alerts_by_status[alert.status].discard(alert.alert_id)
        alert.status = AlertStatus.ESCALATED
        self.alerts_by_status[alert.status].add(alert.alert_id)

        self.escalation_count += 1

        await self._audit_log(
            action="alert_auto_escalated",
            actor="system",
            target={"alert_id": alert.alert_id},
            result="success",
            details={"threat_score": alert.threat_score, "priority": alert.priority.value},
        )
