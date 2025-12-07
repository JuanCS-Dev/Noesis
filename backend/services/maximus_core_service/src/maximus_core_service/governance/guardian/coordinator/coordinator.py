"""Guardian Coordinator.

Central coordinator for all Guardian Agents implementing
Constitutional Enforcement from Anexo D.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from ..article_ii_guardian import ArticleIIGuardian
from ..article_iii_guardian import ArticleIIIGuardian
from ..article_iv_guardian import ArticleIVGuardian
from ..article_v import ArticleVGuardian
from ..base import (
    ConstitutionalViolation,
    GuardianAgent,
    GuardianIntervention,
    GuardianPriority,
    VetoAction,
)
from .alerter import AlertManager
from .analyzer import PatternAnalyzer
from .conflict import ConflictResolver
from .models import CoordinatorMetrics
from .reporter import ComplianceReporter

logger = logging.getLogger(__name__)


class GuardianCoordinator:
    """Central coordinator for all Guardian Agents.

    Responsibilities:
    - Start/stop all Guardians
    - Aggregate and prioritize violations
    - Resolve conflicts between Guardians
    - Generate unified compliance reports
    - Manage veto escalations
    - Provide API for external systems

    Attributes:
        coordinator_id: Unique identifier.
        guardians: Dictionary of Guardian agents.
        metrics: Coordinator metrics.
    """

    def __init__(
        self,
        guardians: dict[str, GuardianAgent] | None = None,
    ) -> None:
        """Initialize Guardian Coordinator.

        Args:
            guardians: Optional dict of guardian agents.
        """
        self.coordinator_id = "guardian-coordinator-central"

        self.guardians: dict[str, GuardianAgent] = guardians or {
            "article_ii": ArticleIIGuardian(),
            "article_iii": ArticleIIIGuardian(),
            "article_iv": ArticleIVGuardian(),
            "article_v": ArticleVGuardian(),
        }

        self.all_violations: list[ConstitutionalViolation] = []
        self.all_interventions: list[GuardianIntervention] = []
        self.all_vetos: list[VetoAction] = []

        self.metrics = CoordinatorMetrics()

        self._conflict_resolver = ConflictResolver()
        self._analyzer = PatternAnalyzer(self.metrics)
        self._alerter = AlertManager(self.coordinator_id)
        self._reporter = ComplianceReporter(self.metrics, self.guardians)

        self._analyzer.set_pattern_callback(self._handle_violation)
        self._analyzer.set_critical_alert_callback(self._alerter.send_critical_alert)

        self._is_active = False
        self._coordination_task: asyncio.Task[None] | None = None
        self._monitor_interval = 30

        self.veto_escalation_threshold = 3

    async def start(self) -> None:
        """Start all Guardian Agents and coordinator."""
        if self._is_active:
            return

        self._is_active = True

        for guardian in self.guardians.values():
            guardian.register_violation_callback(self._handle_violation)
            guardian.register_intervention_callback(self._handle_intervention)
            guardian.register_veto_callback(self._handle_veto)
            await guardian.start()

        self._coordination_task = asyncio.create_task(self._coordination_loop())

        logger.info(
            "Guardian Coordinator started at %s",
            datetime.utcnow().isoformat(),
        )

    async def stop(self) -> None:
        """Stop all Guardian Agents and coordinator."""
        self._is_active = False

        if self._coordination_task:
            self._coordination_task.cancel()
            try:
                await self._coordination_task
            except asyncio.CancelledError:
                pass

        for guardian in self.guardians.values():
            await guardian.stop()

        logger.info(
            "Guardian Coordinator stopped at %s",
            datetime.utcnow().isoformat(),
        )

    async def _coordination_loop(self) -> None:
        """Main coordination loop."""
        while self._is_active:
            try:
                await self._analyzer.analyze_violation_patterns(self.all_violations)

                self._conflict_resolver.resolve_conflicts(self.all_violations)

                self._analyzer.update_metrics(self.all_violations)

                await self._analyzer.check_critical_thresholds(
                    self.all_violations,
                    self.all_vetos,
                )

                await asyncio.sleep(self._monitor_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Coordination error: %s", e)

    async def _handle_violation(
        self,
        violation: ConstitutionalViolation,
    ) -> None:
        """Handle violation from a Guardian.

        Args:
            violation: The detected violation.
        """
        self.all_violations.append(violation)

        article = violation.article.value
        self.metrics.violations_by_article[article] = (
            self.metrics.violations_by_article.get(article, 0) + 1
        )

        severity = violation.severity.value
        self.metrics.violations_by_severity[severity] = (
            self.metrics.violations_by_severity.get(severity, 0) + 1
        )

        self.metrics.total_violations_detected += 1

        if violation.severity == GuardianPriority.CRITICAL:
            await self._alerter.send_critical_alert(violation)

    async def _handle_intervention(
        self,
        intervention: GuardianIntervention,
    ) -> None:
        """Handle intervention from a Guardian.

        Args:
            intervention: The intervention made.
        """
        self.all_interventions.append(intervention)
        self.metrics.interventions_made += 1

    async def _handle_veto(self, veto: VetoAction) -> None:
        """Handle veto from a Guardian.

        Args:
            veto: The veto action.
        """
        self.all_vetos.append(veto)
        self.metrics.vetos_enacted += 1

        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        recent_vetos = [v for v in self.all_vetos if v.enacted_at > cutoff_time]

        if len(recent_vetos) >= self.veto_escalation_threshold:
            await self._alerter.escalate_vetos(recent_vetos)

    def get_status(self) -> dict[str, Any]:
        """Get coordinator status.

        Returns:
            Status dictionary.
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=1)

        return {
            "coordinator_id": self.coordinator_id,
            "is_active": self._is_active,
            "guardians": {
                name: {
                    "id": guardian.guardian_id,
                    "active": guardian.is_active(),
                    "stats": guardian.get_statistics(),
                }
                for name, guardian in self.guardians.items()
            },
            "metrics": self.metrics.to_dict(),
            "active_vetos": len([v for v in self.all_vetos if v.is_active()]),
            "recent_violations": len([
                v for v in self.all_violations if v.detected_at > cutoff_time
            ]),
        }

    def generate_compliance_report(
        self,
        period_hours: int = 24,
    ) -> dict[str, Any]:
        """Generate unified compliance report.

        Args:
            period_hours: Report period in hours.

        Returns:
            Complete compliance report.
        """
        return self._reporter.generate_compliance_report(
            violations=self.all_violations,
            interventions=self.all_interventions,
            vetos=self.all_vetos,
            period_hours=period_hours,
        )

    async def override_veto(
        self,
        veto_id: str,
        override_reason: str,
        approver_id: str,
    ) -> bool:
        """Override a Guardian veto.

        Args:
            veto_id: ID of veto to override.
            override_reason: Justification for override.
            approver_id: ID of human approver.

        Returns:
            True if override successful.
        """
        veto = next((v for v in self.all_vetos if v.veto_id == veto_id), None)

        if not veto:
            return False

        if not veto.override_allowed:
            logger.warning("Veto %s cannot be overridden", veto_id)
            return False

        veto.metadata["overridden"] = True
        veto.metadata["override_reason"] = override_reason
        veto.metadata["override_approver"] = approver_id
        veto.metadata["override_time"] = datetime.utcnow().isoformat()

        logger.info(
            "Veto %s overridden by %s: %s",
            veto_id,
            approver_id,
            override_reason,
        )

        return True

    @property
    def conflict_resolutions(self) -> list:
        """Get all conflict resolutions.

        Returns:
            List of conflict resolutions.
        """
        return self._conflict_resolver.conflict_resolutions
