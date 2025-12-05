"""
Ethical Audit Service - Violation Detector
==========================================

Detects violations of constitutional principles.
"""

from __future__ import annotations


import uuid
from typing import List

from config import AuditSettings
from models.audit import ComplianceReport, Violation
from utils.logging_config import get_logger

logger = get_logger(__name__)


class ViolationDetector:
    """
    Detects and reports constitutional violations.

    Attributes:
        settings: Audit settings
        violation_history: Historical violations
    """

    def __init__(self, settings: AuditSettings):
        """
        Initialize Violation Detector.

        Args:
            settings: Audit settings
        """
        self.settings = settings
        self.violation_history: List[Violation] = []
        logger.info("violation_detector_initialized")

    async def record_violation(self, violation: Violation) -> None:
        """
        Record a constitutional violation.

        Args:
            violation: Violation to record
        """
        self.violation_history.append(violation)
        logger.warning(
            "violation_recorded",
            violation_id=violation.violation_id,
            violation_type=violation.violation_type.value,
            severity=violation.severity.value,
            service=violation.service
        )

    async def generate_compliance_report(
        self,
        service: str,
        total_checks: int
    ) -> ComplianceReport:
        """
        Generate compliance report for a service.

        Args:
            service: Service name
            total_checks: Total checks performed

        Returns:
            Compliance report
        """
        # Get violations for this service
        service_violations = [
            v for v in self.violation_history
            if v.service == service
        ]

        passed_checks = total_checks - len(service_violations)

        # Calculate compliance score
        if total_checks > 0:
            compliance_score = passed_checks / total_checks
        else:
            compliance_score = 1.0

        report = ComplianceReport(
            report_id=str(uuid.uuid4()),
            service=service,
            total_checks=total_checks,
            passed_checks=passed_checks,
            violations=service_violations,
            compliance_score=compliance_score
        )

        logger.info(
            "compliance_report_generated",
            report_id=report.report_id,
            service=service,
            compliance_score=compliance_score
        )

        return report

    async def clear_history(self, service: str | None = None) -> int:
        """
        Clear violation history.

        Args:
            service: Service to clear (None for all)

        Returns:
            Number of violations cleared
        """
        if service is None:
            count = len(self.violation_history)
            self.violation_history.clear()
        else:
            initial_count = len(self.violation_history)
            self.violation_history = [
                v for v in self.violation_history
                if v.service != service
            ]
            count = initial_count - len(self.violation_history)

        logger.info("violation_history_cleared", count=count, service=service)
        return count
