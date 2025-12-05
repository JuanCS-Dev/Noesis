"""
Query Engine Mixin for Audit Trail.

Provides querying and filtering capabilities for audit entries.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..base_pkg import AuditEntry

if TYPE_CHECKING:
    from .models import AuditQuery


class QueryMixin:
    """
    Mixin for querying audit trail entries.

    Provides filtering, sorting, and pagination capabilities.
    """

    def query(self, query: AuditQuery) -> list[AuditEntry]:
        """
        Query audit trail with filters.

        Args:
            query: Query parameters

        Returns:
            Filtered audit entries
        """
        results = self._audit_log.copy()

        # Time range filter
        if query.start_time:
            results = [e for e in results if e.timestamp >= query.start_time]
        if query.end_time:
            results = [e for e in results if e.timestamp <= query.end_time]

        # Decision ID filter
        if query.decision_ids:
            results = [e for e in results if e.decision_id in query.decision_ids]

        # Risk level filter
        if query.risk_levels:
            results = [e for e in results if e.risk_level in query.risk_levels]

        # Automation level filter
        if query.automation_levels:
            results = [e for e in results if e.automation_level in query.automation_levels]

        # Status filter (using decision snapshots)
        if query.statuses:
            status_values = [s.value for s in query.statuses]
            results = [
                e
                for e in results
                if e.decision_snapshot.get("status") in status_values
            ]

        # Operator ID filter
        if query.operator_ids:
            results = [e for e in results if e.actor_id in query.operator_ids]

        # Actor type filter
        if query.actor_types:
            results = [e for e in results if e.actor_type in query.actor_types]

        # Event type filter
        if query.event_types:
            results = [e for e in results if e.event_type in query.event_types]

        # Compliance tag filter
        if query.compliance_tags:
            results = [
                e
                for e in results
                if any(tag in e.compliance_tags for tag in query.compliance_tags)
            ]

        # Sorting
        reverse = query.sort_order == "desc"
        if query.sort_by == "timestamp":
            results.sort(key=lambda e: e.timestamp, reverse=reverse)
        elif query.sort_by == "risk_level":
            risk_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "NONE": 0}
            results.sort(
                key=lambda e: risk_order.get(e.risk_level.value, 0), reverse=reverse
            )
        elif query.sort_by == "decision_id":
            results.sort(key=lambda e: e.decision_id, reverse=reverse)

        # Pagination
        start = query.offset
        end = query.offset + query.limit
        paginated = results[start:end]

        self.logger.info(
            "Query executed: found %d entries (total=%d, offset=%d, limit=%d)",
            len(paginated),
            len(results),
            query.offset,
            query.limit,
        )

        return paginated
