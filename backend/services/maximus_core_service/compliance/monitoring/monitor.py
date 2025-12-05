"""Compliance Monitor.

Main compliance monitoring system combining all functionality.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from datetime import datetime, timedelta

from ..base import (
    ComplianceConfig,
    ViolationSeverity,
)
from ..compliance_engine import ComplianceEngine
from ..evidence_collector import EvidenceCollector
from ..gap_analyzer import GapAnalyzer
from .checkers import ComplianceCheckerMixin
from .metrics import MetricsMixin
from .models import ComplianceAlert, MonitoringMetrics

logger = logging.getLogger(__name__)


class ComplianceMonitor(ComplianceCheckerMixin, MetricsMixin):
    """Continuous compliance monitoring system.

    Monitors compliance status, detects violations, and sends alerts.

    Attributes:
        engine: Compliance engine instance.
        evidence_collector: Evidence collector instance.
        gap_analyzer: Gap analyzer instance.
        config: Compliance configuration.
    """

    def __init__(
        self,
        compliance_engine: ComplianceEngine,
        evidence_collector: EvidenceCollector | None = None,
        gap_analyzer: GapAnalyzer | None = None,
        config: ComplianceConfig | None = None,
    ) -> None:
        """Initialize compliance monitor.

        Args:
            compliance_engine: Compliance engine instance.
            evidence_collector: Optional evidence collector.
            gap_analyzer: Optional gap analyzer.
            config: Compliance configuration.
        """
        self.engine = compliance_engine
        self.evidence_collector = evidence_collector
        self.gap_analyzer = gap_analyzer
        self.config = config or ComplianceConfig()

        self._monitoring = False
        self._monitor_thread: threading.Thread | None = None
        self._alerts: list[ComplianceAlert] = []
        self._metrics_history: list[MonitoringMetrics] = []
        self._alert_handlers: list[Callable[[ComplianceAlert], None]] = []

        logger.info("Compliance monitor initialized")

    def register_alert_handler(
        self,
        handler: Callable[[ComplianceAlert], None],
    ) -> None:
        """Register alert handler callback.

        Args:
            handler: Function to call when alert is triggered.
        """
        self._alert_handlers.append(handler)
        logger.info("Registered alert handler: %s", handler.__name__)

    def start_monitoring(self, check_interval_seconds: int = 3600) -> None:
        """Start continuous compliance monitoring.

        Args:
            check_interval_seconds: Interval between checks (default 1 hour).
        """
        if self._monitoring:
            logger.warning("Monitoring already started")
            return

        self._monitoring = True

        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(check_interval_seconds,),
            daemon=True,
            name="compliance-monitor",
        )
        self._monitor_thread.start()

        logger.info(
            "Compliance monitoring started (interval: %ds)", check_interval_seconds
        )

    def stop_monitoring(self) -> None:
        """Stop compliance monitoring."""
        if not self._monitoring:
            return

        self._monitoring = False

        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=10)

        logger.info("Compliance monitoring stopped")

    def _monitoring_loop(self, check_interval: int) -> None:
        """Main monitoring loop.

        Args:
            check_interval: Seconds between checks.
        """
        logger.info("Monitoring loop started")

        while self._monitoring:
            try:
                self._run_monitoring_checks()
                time.sleep(check_interval)

            except Exception as e:
                logger.error("Error in monitoring loop: %s", e, exc_info=True)
                time.sleep(60)

        logger.info("Monitoring loop stopped")

    def _run_monitoring_checks(self) -> None:
        """Run all monitoring checks."""
        logger.debug("Running monitoring checks")

        evidence_by_regulation = None
        if self.evidence_collector:
            all_evidence = self.evidence_collector.get_all_evidence()
            evidence_by_regulation = {
                reg_type: all_evidence for reg_type in self.config.enabled_regulations
            }

        snapshot = self.engine.run_all_checks(evidence_by_regulation)

        self._check_compliance_thresholds(snapshot)
        self._detect_violations(snapshot)

        if self.evidence_collector:
            self._check_evidence_expiration()

        metrics = self._calculate_metrics(snapshot)
        self._metrics_history.append(metrics)

        cutoff = datetime.utcnow() - timedelta(days=30)
        self._metrics_history = [
            m for m in self._metrics_history if m.timestamp > cutoff
        ]

        logger.debug("Monitoring checks complete, %d total alerts", len(self._alerts))

    def get_alerts(
        self,
        alert_type: str | None = None,
        acknowledged: bool | None = None,
        severity: ViolationSeverity | None = None,
    ) -> list[ComplianceAlert]:
        """Get alerts filtered by criteria.

        Args:
            alert_type: Optional filter by alert type.
            acknowledged: Optional filter by acknowledged status.
            severity: Optional filter by severity.

        Returns:
            List of matching alerts.
        """
        alerts = self._alerts

        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]

        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        return alerts

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge alert.

        Args:
            alert_id: Alert ID.
            acknowledged_by: User acknowledging.

        Returns:
            True if successful.
        """
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.acknowledge(acknowledged_by)
                logger.info("Alert %s acknowledged by %s", alert_id, acknowledged_by)
                return True

        return False
