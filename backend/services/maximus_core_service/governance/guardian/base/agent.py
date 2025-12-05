"""Guardian Agent Base Class.

Abstract base class for Constitutional Guardian Agents.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from typing import Any

from .enums import ConstitutionalArticle, GuardianPriority, InterventionType
from .models import (
    ConstitutionalViolation,
    GuardianDecision,
    GuardianIntervention,
    GuardianReport,
    VetoAction,
)


class GuardianAgent(ABC):
    """Abstract base class for Constitutional Guardian Agents.

    Each Guardian enforces specific Articles of the Vértice Constitution
    through continuous monitoring, detection, and intervention.

    Attributes:
        guardian_id: Unique identifier for the guardian.
        article: Constitutional article this guardian enforces.
        name: Human-readable name.
        description: Description of guardian's purpose.
    """

    def __init__(
        self,
        guardian_id: str,
        article: ConstitutionalArticle,
        name: str,
        description: str,
    ) -> None:
        """Initialize Guardian Agent.

        Args:
            guardian_id: Unique identifier.
            article: Constitutional article to enforce.
            name: Human-readable name.
            description: Guardian description.
        """
        self.guardian_id = guardian_id
        self.article = article
        self.name = name
        self.description = description

        self._is_active = False
        self._monitor_task: asyncio.Task[None] | None = None
        self._monitor_interval = 60

        self._violations: list[ConstitutionalViolation] = []
        self._interventions: list[GuardianIntervention] = []
        self._vetos: list[VetoAction] = []
        self._decisions: list[GuardianDecision] = []

        self._violation_callbacks: list[
            Callable[[ConstitutionalViolation], Awaitable[None]]
        ] = []
        self._intervention_callbacks: list[
            Callable[[GuardianIntervention], Awaitable[None]]
        ] = []
        self._veto_callbacks: list[Callable[[VetoAction], Awaitable[None]]] = []

    @abstractmethod
    async def monitor(self) -> list[ConstitutionalViolation]:
        """Monitor the ecosystem for constitutional violations.

        Returns:
            List of detected violations.
        """

    @abstractmethod
    async def analyze_violation(
        self,
        violation: ConstitutionalViolation,
    ) -> GuardianDecision:
        """Analyze a violation and decide on appropriate action.

        Args:
            violation: The detected violation.

        Returns:
            Decision on how to handle the violation.
        """

    @abstractmethod
    async def intervene(
        self,
        violation: ConstitutionalViolation,
    ) -> GuardianIntervention:
        """Take intervention action for a violation.

        Args:
            violation: The violation to address.

        Returns:
            Record of intervention taken.
        """

    @abstractmethod
    def get_monitored_systems(self) -> list[str]:
        """Get list of systems this Guardian monitors.

        Returns:
            List of system identifiers.
        """

    async def start(self) -> None:
        """Start the Guardian Agent monitoring."""
        if self._is_active:
            return

        self._is_active = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())

    async def stop(self) -> None:
        """Stop the Guardian Agent monitoring."""
        self._is_active = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._is_active:
            try:
                violations = await self.monitor()

                for violation in violations:
                    await self._process_violation(violation)

                await asyncio.sleep(self._monitor_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                await self._handle_monitor_error(e)

    async def _process_violation(
        self,
        violation: ConstitutionalViolation,
    ) -> None:
        """Process a detected violation.

        Args:
            violation: The detected violation.
        """
        self._violations.append(violation)

        for callback in self._violation_callbacks:
            await callback(violation)

        decision = await self.analyze_violation(violation)
        self._decisions.append(decision)

        if decision.decision_type in ["block", "veto", "remediate"]:
            intervention = await self.intervene(violation)
            self._interventions.append(intervention)

            for callback in self._intervention_callbacks:
                await callback(intervention)

            if intervention.intervention_type == InterventionType.VETO:
                veto = await self._create_veto(violation, decision)
                self._vetos.append(veto)

                for callback in self._veto_callbacks:
                    await callback(veto)

    async def _create_veto(
        self,
        violation: ConstitutionalViolation,
        decision: GuardianDecision,
    ) -> VetoAction:
        """Create a veto action.

        Args:
            violation: The related violation.
            decision: The guardian decision.

        Returns:
            The created veto action.
        """
        target_system = (
            violation.affected_systems[0] if violation.affected_systems else "unknown"
        )

        return VetoAction(
            guardian_id=self.guardian_id,
            target_action=decision.target,
            target_system=target_system,
            violation=violation,
            reason=decision.reasoning,
            override_allowed=decision.confidence < 0.95,
            override_requirements=[
                "Human architect approval",
                "ERB review if CRITICAL severity",
            ],
            metadata={
                "decision_id": decision.decision_id,
                "confidence": decision.confidence,
            },
        )

    async def _handle_monitor_error(self, error: Exception) -> None:
        """Handle monitoring errors.

        Args:
            error: The error that occurred.
        """
        violation = ConstitutionalViolation(
            article=self.article,
            clause="Guardian Monitoring",
            rule="Guardian must maintain continuous monitoring",
            description=f"Guardian monitoring error: {error!s}",
            severity=GuardianPriority.HIGH,
            affected_systems=[self.guardian_id],
            recommended_action="Investigate and fix Guardian monitoring",
            metadata={"error_type": type(error).__name__},
        )

        await self._process_violation(violation)

    async def veto_action(
        self,
        action: str,
        system: str,
        reason: str,
        duration_hours: int | None = None,
    ) -> VetoAction:
        """Exercise veto power to block an action.

        Args:
            action: Action to veto.
            system: System where action occurs.
            reason: Constitutional reason for veto.
            duration_hours: Hours until veto expires.

        Returns:
            The veto action taken.
        """
        expires_at = None
        if duration_hours:
            expires_at = datetime.utcnow() + timedelta(hours=duration_hours)

        veto = VetoAction(
            guardian_id=self.guardian_id,
            target_action=action,
            target_system=system,
            reason=reason,
            expires_at=expires_at,
            override_allowed=True,
            override_requirements=[
                f"Approval from {self.article.value} Guardian administrator",
                "Constitutional justification required",
            ],
        )

        self._vetos.append(veto)

        for callback in self._veto_callbacks:
            await callback(veto)

        return veto

    def get_active_vetos(self) -> list[VetoAction]:
        """Get all active vetos.

        Returns:
            List of active vetos.
        """
        return [v for v in self._vetos if v.is_active()]

    def generate_report(self, period_hours: int = 24) -> GuardianReport:
        """Generate compliance report for specified period.

        Args:
            period_hours: Hours to include in report.

        Returns:
            Guardian compliance report.
        """
        period_start = datetime.utcnow() - timedelta(hours=period_hours)
        period_end = datetime.utcnow()

        period_violations = [
            v for v in self._violations if period_start <= v.detected_at <= period_end
        ]
        period_interventions = [
            i for i in self._interventions if period_start <= i.timestamp <= period_end
        ]
        period_vetos = [
            v for v in self._vetos if period_start <= v.enacted_at <= period_end
        ]

        total_checks = len(period_violations) + 100
        violations_count = len(period_violations)
        compliance_score = ((total_checks - violations_count) / total_checks) * 100

        violation_counts: dict[str, int] = {}
        for v in period_violations:
            key = f"{v.clause}: {v.rule}"
            violation_counts[key] = violation_counts.get(key, 0) + 1

        top_violations = sorted(
            violation_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]

        recommendations = self._generate_recommendations(
            violations_count, period_vetos, compliance_score
        )

        avg_confidence = 0.0
        if self._decisions:
            avg_confidence = sum(d.confidence for d in self._decisions) / len(
                self._decisions
            )

        return GuardianReport(
            guardian_id=self.guardian_id,
            period_start=period_start,
            period_end=period_end,
            violations_detected=violations_count,
            interventions_made=len(period_interventions),
            vetos_enacted=len(period_vetos),
            compliance_score=compliance_score,
            top_violations=[f"{v[0]} ({v[1]} occurrences)" for v in top_violations],
            recommendations=recommendations,
            metrics={
                "average_confidence": avg_confidence,
                "critical_violations": sum(
                    1
                    for v in period_violations
                    if v.severity == GuardianPriority.CRITICAL
                ),
                "auto_remediated": sum(
                    1
                    for i in period_interventions
                    if i.intervention_type == InterventionType.REMEDIATION
                ),
            },
        )

    def _generate_recommendations(
        self,
        violations_count: int,
        period_vetos: list[VetoAction],
        compliance_score: float,
    ) -> list[str]:
        """Generate recommendations based on metrics.

        Args:
            violations_count: Number of violations.
            period_vetos: List of vetos in period.
            compliance_score: Current compliance score.

        Returns:
            List of recommendations.
        """
        recommendations = []

        if violations_count > 10:
            recommendations.append(
                "High violation rate detected - review development practices"
            )
        if len(period_vetos) > 0:
            recommendations.append(
                f"{len(period_vetos)} vetos enacted - ensure teams understand Constitution"
            )
        if compliance_score < 90:
            recommendations.append(
                "Compliance below target - mandatory Constitution training recommended"
            )

        return recommendations

    def register_violation_callback(
        self,
        callback: Callable[[ConstitutionalViolation], Awaitable[None]],
    ) -> None:
        """Register callback for violation notifications.

        Args:
            callback: Async callback function.
        """
        self._violation_callbacks.append(callback)

    def register_intervention_callback(
        self,
        callback: Callable[[GuardianIntervention], Awaitable[None]],
    ) -> None:
        """Register callback for intervention notifications.

        Args:
            callback: Async callback function.
        """
        self._intervention_callbacks.append(callback)

    def register_veto_callback(
        self,
        callback: Callable[[VetoAction], Awaitable[None]],
    ) -> None:
        """Register callback for veto notifications.

        Args:
            callback: Async callback function.
        """
        self._veto_callbacks.append(callback)

    def is_active(self) -> bool:
        """Check if Guardian is actively monitoring.

        Returns:
            True if active.
        """
        return self._is_active

    def get_statistics(self) -> dict[str, Any]:
        """Get Guardian statistics.

        Returns:
            Statistics dictionary.
        """
        return {
            "guardian_id": self.guardian_id,
            "name": self.name,
            "article": self.article.value,
            "is_active": self._is_active,
            "total_violations": len(self._violations),
            "total_interventions": len(self._interventions),
            "active_vetos": len(self.get_active_vetos()),
            "total_decisions": len(self._decisions),
            "monitored_systems": self.get_monitored_systems(),
        }

    def __repr__(self) -> str:
        """String representation.

        Returns:
            String representation.
        """
        return (
            f"GuardianAgent(id={self.guardian_id}, "
            f"name={self.name}, "
            f"article={self.article.value}, "
            f"active={self._is_active})"
        )
