"""Compliance Monitoring Checkers.

Mixin providing compliance checking functionality.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timedelta

from ..base import (
    ComplianceConfig,
    ComplianceViolation,
    ViolationSeverity,
)
from ..compliance_engine import ComplianceSnapshot
from ..evidence_collector import EvidenceCollector
from .models import ComplianceAlert

logger = logging.getLogger(__name__)


class ComplianceCheckerMixin:
    """Mixin providing compliance checking methods.

    Handles threshold checks, violation detection, and evidence expiration.

    Attributes:
        config: Compliance configuration.
        evidence_collector: Evidence collector instance.
        _alerts: List of alerts.
        _alert_handlers: List of alert handlers.
    """

    config: ComplianceConfig
    evidence_collector: EvidenceCollector | None
    _alerts: list[ComplianceAlert]
    _alert_handlers: list[Callable[[ComplianceAlert], None]]

    def _check_compliance_thresholds(self, snapshot: ComplianceSnapshot) -> None:
        """Check if compliance is below configured thresholds.

        Args:
            snapshot: Compliance snapshot.
        """
        threshold = self.config.alert_threshold_percentage

        if snapshot.overall_compliance_percentage < threshold:
            alert = ComplianceAlert(
                alert_type="threshold_breach",
                severity=ViolationSeverity.HIGH,
                title="Overall Compliance Below Threshold",
                message=(
                    f"Overall compliance is {snapshot.overall_compliance_percentage:.1f}%, "
                    f"below threshold of {threshold}%"
                ),
                metadata={
                    "current_compliance": snapshot.overall_compliance_percentage,
                    "threshold": threshold,
                    "snapshot_id": snapshot.snapshot_id,
                },
            )
            self._send_alert(alert)

        for reg_type, result in snapshot.regulation_results.items():
            if result.compliance_percentage < threshold:
                alert = ComplianceAlert(
                    alert_type="threshold_breach",
                    severity=ViolationSeverity.MEDIUM,
                    title=f"{reg_type.value} Compliance Below Threshold",
                    message=(
                        f"{reg_type.value} compliance is {result.compliance_percentage:.1f}%, "
                        f"below threshold of {threshold}%"
                    ),
                    regulation_type=reg_type,
                    metadata={
                        "current_compliance": result.compliance_percentage,
                        "threshold": threshold,
                    },
                )
                self._send_alert(alert)

    def _detect_violations(self, snapshot: ComplianceSnapshot) -> None:
        """Detect new violations.

        Args:
            snapshot: Compliance snapshot.
        """
        for reg_type, result in snapshot.regulation_results.items():
            for violation in result.violations:
                if not self._is_violation_alerted(violation):
                    alert = ComplianceAlert(
                        alert_type="violation",
                        severity=violation.severity,
                        title=violation.title,
                        message=violation.description,
                        regulation_type=reg_type,
                        metadata={
                            "violation_id": violation.violation_id,
                            "control_id": violation.control_id,
                        },
                    )

                    if (
                        violation.severity == ViolationSeverity.CRITICAL
                        and self.config.alert_critical_violations_immediately
                    ):
                        self._send_alert(alert)

    def _check_evidence_expiration(self) -> None:
        """Check for expired or expiring evidence."""
        if not self.evidence_collector:
            return

        expired = self.evidence_collector.get_expired_evidence()

        if expired:
            alert = ComplianceAlert(
                alert_type="evidence_expiring",
                severity=ViolationSeverity.MEDIUM,
                title="Evidence Has Expired",
                message=f"{len(expired)} evidence items have expired and need renewal",
                metadata={
                    "expired_count": len(expired),
                    "evidence_ids": [e.evidence_id for e in expired],
                },
            )
            self._send_alert(alert)

        all_evidence = self.evidence_collector.get_all_evidence()
        expiring_soon = []
        threshold_date = datetime.utcnow() + timedelta(days=30)

        for evidence_list in all_evidence.values():
            for evidence in evidence_list:
                if (
                    evidence.expiration_date
                    and evidence.expiration_date < threshold_date
                    and not evidence.is_expired()
                ):
                    expiring_soon.append(evidence)

        if expiring_soon:
            alert = ComplianceAlert(
                alert_type="evidence_expiring",
                severity=ViolationSeverity.LOW,
                title="Evidence Expiring Soon",
                message=f"{len(expiring_soon)} evidence items will expire in next 30 days",
                metadata={
                    "expiring_count": len(expiring_soon),
                    "evidence_ids": [e.evidence_id for e in expiring_soon],
                },
            )
            self._send_alert(alert)

    def _send_alert(self, alert: ComplianceAlert) -> None:
        """Send alert through registered handlers.

        Args:
            alert: Alert to send.
        """
        self._alerts.append(alert)

        if len(self._alerts) > 1000:
            self._alerts = self._alerts[-1000:]

        logger.warning(
            "COMPLIANCE ALERT [%s]: %s - %s",
            alert.severity.value.upper(),
            alert.title,
            alert.message,
        )

        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error("Alert handler %s failed: %s", handler.__name__, e)

    def _is_violation_alerted(self, violation: ComplianceViolation) -> bool:
        """Check if violation has already been alerted.

        Args:
            violation: Violation to check.

        Returns:
            True if already alerted.
        """
        for alert in self._alerts:
            if alert.alert_type == "violation":
                if alert.metadata.get("violation_id") == violation.violation_id:
                    return True
        return False
