"""
Compliance Reporting Mixin for Audit Trail.

Generates compliance reports for regulatory requirements.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from .models import ComplianceReport

if TYPE_CHECKING:
    from ..base_pkg import AuditEntry


class ComplianceReportingMixin:
    """
    Mixin for generating compliance reports.

    Provides regulatory compliance reporting for HITL decisions.
    """

    def generate_compliance_report(
        self,
        start_time: datetime,
        end_time: datetime,
        include_entries: bool = False,
    ) -> ComplianceReport:
        """
        Generate compliance report for period.

        Args:
            start_time: Report period start
            end_time: Report period end
            include_entries: Whether to include full audit entries

        Returns:
            ComplianceReport
        """
        report = ComplianceReport(
            report_id=f"compliance-{uuid.uuid4().hex[:12]}",
            period_start=start_time,
            period_end=end_time,
        )

        # Filter entries by time range
        entries = [
            e for e in self._audit_log if start_time <= e.timestamp <= end_time
        ]

        if include_entries:
            report.audit_entries = entries

        # Track operator IDs and review times
        operator_ids = set()
        review_times = []

        # Aggregate statistics
        for entry in entries:
            # Count by event type
            if entry.event_type == "decision_created":
                report.total_decisions += 1

                # Risk breakdown
                risk_level = entry.risk_level.value
                if risk_level == "CRITICAL":
                    report.critical_decisions += 1
                elif risk_level == "HIGH":
                    report.high_risk_decisions += 1
                elif risk_level == "MEDIUM":
                    report.medium_risk_decisions += 1
                elif risk_level == "LOW":
                    report.low_risk_decisions += 1

            elif entry.event_type == "decision_executed":
                report.auto_executed += 1

            elif entry.event_type in ["decision_approved", "decision_rejected"]:
                report.human_reviewed += 1

                # Track operator stats
                if entry.actor_id:
                    operator_ids.add(entry.actor_id)

                # Track review time
                review_time = entry.context_snapshot.get("review_time_seconds")
                if review_time:
                    review_times.append(review_time)

            if entry.event_type == "decision_approved":
                report.approved += 1
            elif entry.event_type == "decision_rejected":
                report.rejected += 1
            elif entry.event_type == "decision_escalated":
                report.escalated += 1

        # Calculate metrics
        report.unique_operators = len(operator_ids)

        if report.total_decisions > 0:
            report.automation_rate = report.auto_executed / report.total_decisions
            report.human_oversight_rate = report.human_reviewed / report.total_decisions
            report.sla_compliance_rate = 1.0 - (report.sla_violations / report.total_decisions)

        if review_times:
            report.average_review_time = sum(review_times) / len(review_times)

        self.logger.info(
            "Compliance report generated: %s (period=%s to %s, decisions=%d)",
            report.report_id,
            start_time,
            end_time,
            report.total_decisions,
        )

        return report
