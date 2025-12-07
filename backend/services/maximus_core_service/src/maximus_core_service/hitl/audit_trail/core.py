"""
Core Audit Trail Implementation.

Base class with initialization and helper methods.
"""

from __future__ import annotations

import logging
from typing import Any

from ..base_pkg import AuditEntry, AutomationLevel, HITLDecision, RiskLevel
from .compliance import ComplianceReportingMixin
from .event_logger import EventLoggingMixin
from .query_engine import QueryMixin


class AuditTrail(EventLoggingMixin, QueryMixin, ComplianceReportingMixin):
    """
    Immutable audit trail for HITL decisions.

    Logs all decision events, operator actions, and system events for
    compliance, forensics, and analytics.

    Inherits from:
        - EventLoggingMixin: log_decision_* methods
        - QueryMixin: query method
        - ComplianceReportingMixin: generate_compliance_report method
    """

    def __init__(self, storage_backend: Any | None = None) -> None:
        """
        Initialize audit trail.

        Args:
            storage_backend: Storage backend for persistence (e.g., database, S3)
                           If None, uses in-memory storage
        """
        self.storage_backend = storage_backend
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # In-memory storage (if no backend)
        self._audit_log: list[AuditEntry] = []

        # PII fields to redact
        self._pii_fields = [
            "context_snapshot.user_email",
            "context_snapshot.user_name",
            "context_snapshot.ip_address",
            "decision_snapshot.metadata.pii_data",
        ]

        # Metrics
        self.metrics = {
            "total_entries": 0,
            "decision_created": 0,
            "decision_executed": 0,
            "decision_approved": 0,
            "decision_rejected": 0,
            "decision_escalated": 0,
            "decision_failed": 0,
        }

        self.logger.info("Audit Trail initialized")

    def _snapshot_decision(self, decision: HITLDecision) -> dict[str, Any]:
        """
        Create snapshot of decision for audit.

        Args:
            decision: HITL decision to snapshot

        Returns:
            Decision snapshot dictionary
        """
        return {
            "decision_id": decision.decision_id,
            "action_type": decision.context.action_type.value,
            "action_params": decision.context.action_params,
            "risk_level": decision.risk_level.value,
            "automation_level": decision.automation_level.value,
            "status": decision.status.value,
            "confidence": decision.context.confidence,
            "threat_score": decision.context.threat_score,
            "created_at": decision.created_at.isoformat(),
        }

    def _get_compliance_tags(self, decision: HITLDecision) -> list[str]:
        """
        Get compliance tags for decision.

        Args:
            decision: HITL decision

        Returns:
            List of compliance tags
        """
        tags = []

        # Risk-based tags
        if decision.risk_level == RiskLevel.CRITICAL:
            tags.append("critical_risk")
        elif decision.risk_level == RiskLevel.HIGH:
            tags.append("high_risk")

        # Automation tags
        if decision.automation_level == AutomationLevel.FULL:
            tags.append("automated_decision")
        else:
            tags.append("human_oversight_required")

        # Data sensitivity tags
        if "pii" in decision.metadata.get("data_type", ""):
            tags.append("pii_involved")

        return tags

    def _store_entry(self, entry: AuditEntry) -> None:
        """
        Store audit entry.

        Args:
            entry: Audit entry to store
        """
        # In-memory storage
        self._audit_log.append(entry)

        # External storage backend
        if self.storage_backend:
            try:
                self.storage_backend.store(entry)
            except Exception as e:
                self.logger.error("Failed to store audit entry: %s", e, exc_info=True)

        self.metrics["total_entries"] += 1

        self.logger.debug(
            "Audit entry stored: %s (decision=%s)", entry.event_type, entry.decision_id
        )

    def get_metrics(self) -> dict[str, Any]:
        """
        Get audit trail metrics.

        Returns:
            Metrics dictionary
        """
        return self.metrics.copy()
