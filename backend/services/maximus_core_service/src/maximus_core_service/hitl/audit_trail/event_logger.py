"""
Event Logging Mixin for Audit Trail.

Contains all event logging methods for HITL decision lifecycle.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..base_pkg import AuditEntry

if TYPE_CHECKING:
    from ..base_pkg import HITLDecision, OperatorAction
    from ..risk_assessor import RiskScore


class EventLoggingMixin:
    """
    Mixin for logging HITL decision events.

    Provides methods for logging all decision lifecycle events.
    """

    def log_decision_created(self, decision: HITLDecision, risk_score: RiskScore) -> AuditEntry:
        """
        Log decision creation event.

        Args:
            decision: Created decision
            risk_score: Risk assessment result

        Returns:
            AuditEntry
        """
        entry = AuditEntry(
            decision_id=decision.decision_id,
            event_type="decision_created",
            event_description=f"AI decision created: {decision.context.action_type.value}",
            risk_level=decision.risk_level,
            automation_level=decision.automation_level,
            decision_snapshot=self._snapshot_decision(decision),
            actor_type="ai",
            context_snapshot={
                "risk_factors": {
                    "sensitivity": risk_score.factors.sensitivity_score,
                    "impact": risk_score.factors.impact_score,
                    "complexity": risk_score.factors.complexity_score,
                    "urgency": risk_score.factors.urgency_score,
                    "confidence": risk_score.factors.confidence_score,
                    "precedent": risk_score.factors.precedent_score,
                },
                "risk_score": risk_score.total_score,
                "risk_level": risk_score.risk_level.value,
            },
            compliance_tags=self._get_compliance_tags(decision),
        )

        self._store_entry(entry)
        self.metrics["decision_created"] += 1

        return entry

    def log_decision_queued(self, decision: HITLDecision, queue_priority: int) -> AuditEntry:
        """
        Log decision queued for review.

        Args:
            decision: Queued decision
            queue_priority: Queue priority

        Returns:
            AuditEntry
        """
        entry = AuditEntry(
            decision_id=decision.decision_id,
            event_type="decision_queued",
            event_description=f"Decision queued for human review (priority={queue_priority})",
            risk_level=decision.risk_level,
            automation_level=decision.automation_level,
            decision_snapshot=self._snapshot_decision(decision),
            actor_type="system",
            context_snapshot={
                "queue_priority": queue_priority,
            },
            compliance_tags=self._get_compliance_tags(decision),
        )

        self._store_entry(entry)

        return entry

    def log_decision_executed(self, decision: HITLDecision, execution_result: dict[str, Any]) -> AuditEntry:
        """
        Log decision execution.

        Args:
            decision: Executed decision
            execution_result: Execution result metadata

        Returns:
            AuditEntry
        """
        entry = AuditEntry(
            decision_id=decision.decision_id,
            event_type="decision_executed",
            event_description=f"Decision auto-executed: {decision.context.action_type.value}",
            risk_level=decision.risk_level,
            automation_level=decision.automation_level,
            decision_snapshot=self._snapshot_decision(decision),
            actor_type="ai",
            context_snapshot={"execution_result": execution_result},
            compliance_tags=self._get_compliance_tags(decision),
        )

        self._store_entry(entry)
        self.metrics["decision_executed"] += 1

        return entry

    def log_decision_approved(
        self, decision: HITLDecision, operator_action: OperatorAction
    ) -> AuditEntry:
        """
        Log operator approval.

        Args:
            decision: Approved decision
            operator_action: Operator action details

        Returns:
            AuditEntry
        """
        entry = AuditEntry(
            decision_id=decision.decision_id,
            event_type="decision_approved",
            event_description=f"Decision approved by operator {operator_action.operator_id}",
            risk_level=decision.risk_level,
            automation_level=decision.automation_level,
            decision_snapshot=self._snapshot_decision(decision),
            actor_type="human",
            actor_id=operator_action.operator_id,
            context_snapshot={
                "review_time_seconds": operator_action.review_time_seconds,
                "rationale": operator_action.rationale,
                "modifications": operator_action.modifications,
            },
            compliance_tags=self._get_compliance_tags(decision),
        )

        self._store_entry(entry)
        self.metrics["decision_approved"] += 1

        return entry

    def log_decision_rejected(
        self, decision: HITLDecision, operator_action: OperatorAction
    ) -> AuditEntry:
        """
        Log operator rejection.

        Args:
            decision: Rejected decision
            operator_action: Operator action details

        Returns:
            AuditEntry
        """
        entry = AuditEntry(
            decision_id=decision.decision_id,
            event_type="decision_rejected",
            event_description=f"Decision rejected by operator {operator_action.operator_id}",
            risk_level=decision.risk_level,
            automation_level=decision.automation_level,
            decision_snapshot=self._snapshot_decision(decision),
            actor_type="human",
            actor_id=operator_action.operator_id,
            context_snapshot={
                "review_time_seconds": operator_action.review_time_seconds,
                "rationale": operator_action.rationale,
            },
            compliance_tags=self._get_compliance_tags(decision),
        )

        self._store_entry(entry)
        self.metrics["decision_rejected"] += 1

        return entry

    def log_decision_escalated(
        self, decision: HITLDecision, escalation_reason: str, escalated_to: str
    ) -> AuditEntry:
        """
        Log decision escalation.

        Args:
            decision: Escalated decision
            escalation_reason: Reason for escalation
            escalated_to: Escalation target (operator, supervisor, etc.)

        Returns:
            AuditEntry
        """
        entry = AuditEntry(
            decision_id=decision.decision_id,
            event_type="decision_escalated",
            event_description=f"Decision escalated: {escalation_reason}",
            risk_level=decision.risk_level,
            automation_level=decision.automation_level,
            decision_snapshot=self._snapshot_decision(decision),
            actor_type="system",
            context_snapshot={
                "escalation_reason": escalation_reason,
                "escalated_to": escalated_to,
            },
            compliance_tags=self._get_compliance_tags(decision),
        )

        self._store_entry(entry)
        self.metrics["decision_escalated"] += 1

        return entry

    def log_decision_failed(
        self, decision: HITLDecision, error_message: str, error_details: dict[str, Any]
    ) -> AuditEntry:
        """
        Log decision failure.

        Args:
            decision: Failed decision
            error_message: Error message
            error_details: Error details

        Returns:
            AuditEntry
        """
        entry = AuditEntry(
            decision_id=decision.decision_id,
            event_type="decision_failed",
            event_description=f"Decision failed: {error_message}",
            risk_level=decision.risk_level,
            automation_level=decision.automation_level,
            decision_snapshot=self._snapshot_decision(decision),
            actor_type="system",
            context_snapshot={
                "error_message": error_message,
                "error_details": error_details,
            },
            compliance_tags=self._get_compliance_tags(decision),
        )

        self._store_entry(entry)
        self.metrics["decision_failed"] += 1

        return entry
