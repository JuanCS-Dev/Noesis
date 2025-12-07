"""Compliance Report Generation.

Report generation functionality for compliance engine.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from ..base import RegulationType
from ..regulations import get_regulation

if TYPE_CHECKING:
    from .models import ComplianceCheckResult, ComplianceSnapshot

logger = logging.getLogger(__name__)


def generate_compliance_report(
    snapshot: ComplianceSnapshot,
    start_date: datetime,
    end_date: datetime,
    regulation_types: list[RegulationType] | None = None,
    enabled_regulations: list[RegulationType] | None = None,
) -> dict[str, Any]:
    """Generate compliance report for time period.

    Args:
        snapshot: Compliance snapshot with results.
        start_date: Report start date.
        end_date: Report end date.
        regulation_types: Optional list of regulations (all if None).
        enabled_regulations: List of enabled regulations.

    Returns:
        Compliance report dict.
    """
    regulation_types = regulation_types or enabled_regulations or []

    logger.info(
        "Generating compliance report for %d regulations from %s to %s",
        len(regulation_types),
        start_date.date(),
        end_date.date(),
    )

    filtered_results = {
        reg_type: result
        for reg_type, result in snapshot.regulation_results.items()
        if reg_type in regulation_types
    }

    report = _build_report(start_date, end_date, snapshot, filtered_results)

    logger.info("Compliance report generated: %s", report["report_id"])

    return report


def _build_report(
    start_date: datetime,
    end_date: datetime,
    snapshot: ComplianceSnapshot,
    filtered_results: dict[RegulationType, ComplianceCheckResult],
) -> dict[str, Any]:
    """Build compliance report dictionary.

    Args:
        start_date: Report start date.
        end_date: Report end date.
        snapshot: Compliance snapshot.
        filtered_results: Filtered regulation results.

    Returns:
        Report dictionary.
    """
    report: dict[str, Any] = {
        "report_id": str(uuid.uuid4()),
        "generated_at": datetime.utcnow().isoformat(),
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "summary": {
            "overall_compliance_percentage": snapshot.overall_compliance_percentage,
            "overall_score": snapshot.overall_score,
            "total_violations": snapshot.total_violations,
            "critical_violations": snapshot.critical_violations,
        },
        "regulations": {},
    }

    for reg_type, result in filtered_results.items():
        regulation = get_regulation(reg_type)
        report["regulations"][reg_type.value] = _build_regulation_report(
            regulation, result
        )

    return report


def _build_regulation_report(regulation: Any, result: ComplianceCheckResult) -> dict[str, Any]:
    """Build report section for single regulation.

    Args:
        regulation: Regulation definition.
        result: Compliance check result.

    Returns:
        Regulation report section.
    """
    return {
        "name": regulation.name,
        "version": regulation.version,
        "jurisdiction": regulation.jurisdiction,
        "compliance_percentage": result.compliance_percentage,
        "score": result.score,
        "total_controls": result.total_controls,
        "compliant": result.compliant,
        "non_compliant": result.non_compliant,
        "partially_compliant": result.partially_compliant,
        "violations": [
            {
                "violation_id": v.violation_id,
                "control_id": v.control_id,
                "severity": v.severity.value,
                "title": v.title,
                "description": v.description,
                "detected_at": v.detected_at.isoformat(),
            }
            for v in result.violations
        ],
        "certification_ready": result.is_certification_ready(),
    }
