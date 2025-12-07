"""Article IV Guardian.

Guardian that enforces Article IV: Deliberate Antifragility Principle.
"""

from __future__ import annotations

from typing import Any

from ..base import (
    ConstitutionalArticle,
    ConstitutionalViolation,
    GuardianAgent,
    GuardianDecision,
    GuardianIntervention,
    GuardianPriority,
    InterventionType,
)
from .checkers import AntifragilityCheckerMixin
from .experiments import ChaosExperimentMixin


class ArticleIVGuardian(AntifragilityCheckerMixin, ChaosExperimentMixin, GuardianAgent):
    """Guardian that enforces Article IV: Deliberate Antifragility Principle.

    Monitors for:
    - Lack of chaos engineering tests
    - Missing failure recovery mechanisms
    - Absence of circuit breakers and fallbacks
    - Untested edge cases
    - Experimental features without quarantine
    - Missing resilience patterns

    Attributes:
        chaos_experiments: List of executed chaos experiments.
        quarantined_features: Dict of quarantined features.
        resilience_metrics: Dict of resilience metrics per system.
        test_paths: Paths to check for tests.
        service_paths: Paths to check for services.
    """

    def __init__(
        self,
        test_paths: list[str] | None = None,
        service_paths: list[str] | None = None,
    ) -> None:
        """Initialize Article IV Guardian.

        Args:
            test_paths: Paths to check for chaos tests.
            service_paths: Service paths to check for resilience.
        """
        super().__init__(
            guardian_id="guardian-article-iv",
            article=ConstitutionalArticle.ARTICLE_IV,
            name="Antifragility Guardian",
            description=(
                "Enforces the Deliberate Antifragility Principle, ensuring "
                "the system strengthens from controlled failures and chaos."
            ),
        )

        self.chaos_experiments: list[dict[str, Any]] = []
        self.quarantined_features: dict[str, dict[str, Any]] = {}
        self.resilience_metrics: dict[str, float] = {}

        self.test_paths = test_paths or [
            "/home/juan/vertice-dev/backend/services/maximus_core_service/tests",
            "/home/juan/vertice-dev/backend/services/reactive_fabric_core/tests",
        ]

        self.service_paths = service_paths or [
            "/home/juan/vertice-dev/backend/services/maximus_core_service",
            "/home/juan/vertice-dev/backend/services/reactive_fabric_core",
        ]

        self.resilience_patterns = [
            "circuit_breaker",
            "retry",
            "fallback",
            "timeout",
            "bulkhead",
            "rate_limit",
            "backpressure",
            "graceful_degradation",
        ]

        self.chaos_indicators = [
            "chaos_test",
            "failure_test",
            "stress_test",
            "load_test",
            "resilience_test",
            "fault_injection",
            "network_partition",
        ]

    def get_monitored_systems(self) -> list[str]:
        """Get list of monitored systems.

        Returns:
            List of system identifiers.
        """
        return [
            "chaos_engineering",
            "resilience_framework",
            "experimental_features",
            "fault_tolerance",
            "recovery_mechanisms",
        ]

    async def monitor(self) -> list[ConstitutionalViolation]:
        """Monitor for antifragility violations.

        Returns:
            List of detected violations.
        """
        violations = []

        chaos_violations = await self._check_chaos_engineering()
        violations.extend(chaos_violations)

        resilience_violations = await self._check_resilience_patterns()
        violations.extend(resilience_violations)

        experimental_violations = await self._check_experimental_features()
        violations.extend(experimental_violations)

        recovery_violations = await self._check_failure_recovery()
        violations.extend(recovery_violations)

        fragility_violations = await self._check_system_fragility()
        violations.extend(fragility_violations)

        return violations

    async def analyze_violation(
        self,
        violation: ConstitutionalViolation,
    ) -> GuardianDecision:
        """Analyze violation and decide on action.

        Args:
            violation: The violation to analyze.

        Returns:
            Decision on how to handle the violation.
        """
        if "Insufficient chaos" in violation.description:
            decision_type = "alert"
            confidence = 0.80
            reasoning = (
                "System lacks sufficient chaos testing. "
                "Schedule chaos experiments to improve antifragility."
            )

        elif "Missing resilience patterns" in violation.description:
            decision_type = "block"
            confidence = 0.85
            reasoning = (
                "Critical resilience patterns missing. "
                "System is fragile and will break under stress."
            )

        elif "Experimental feature without quarantine" in violation.description:
            decision_type = "veto"
            confidence = 0.90
            reasoning = (
                "High-risk experimental feature must be quarantined "
                "per Article IV Section 2."
            )

        elif violation.severity == GuardianPriority.HIGH:
            decision_type = "escalate"
            confidence = 0.85
            reasoning = (
                f"Antifragility violation: {violation.rule}. "
                "System resilience at risk."
            )

        else:
            decision_type = "alert"
            confidence = 0.75
            reasoning = (
                "Antifragility could be improved. "
                "Consider adding chaos tests and resilience patterns."
            )

        return GuardianDecision(
            guardian_id=self.guardian_id,
            decision_type=decision_type,
            target=violation.context.get("path", "unknown"),
            reasoning=reasoning,
            confidence=confidence,
            requires_validation=False,
        )

    async def intervene(
        self,
        violation: ConstitutionalViolation,
    ) -> GuardianIntervention:
        """Take intervention action for violation.

        Args:
            violation: The violation to intervene on.

        Returns:
            Intervention result.
        """
        if "Experimental feature" in violation.description:
            intervention_type = InterventionType.VETO
            feature_id = violation.context.get("feature_id", "unknown")
            await self.quarantine_feature(
                feature_id,
                violation.context.get("file", ""),
                "high",
            )
            action_taken = f"Quarantined experimental feature: {feature_id}"

        elif "Insufficient chaos" in violation.description:
            intervention_type = InterventionType.REMEDIATION
            target = (
                violation.affected_systems[0]
                if violation.affected_systems
                else "unknown"
            )
            experiment = await self.run_chaos_experiment(
                "network_latency",
                target,
                {"latency_ms": 500, "duration_s": 60},
            )
            action_taken = f"Initiated chaos experiment: {experiment['id']}"

        elif violation.severity == GuardianPriority.HIGH:
            intervention_type = InterventionType.MONITORING
            target = (
                violation.affected_systems[0]
                if violation.affected_systems
                else "unknown"
            )
            action_taken = (
                f"Increased resilience monitoring on {target} "
                "to detect fragility"
            )

        else:
            intervention_type = InterventionType.ALERT
            action_taken = f"Alert: {violation.description}"

        return GuardianIntervention(
            guardian_id=self.guardian_id,
            intervention_type=intervention_type,
            priority=violation.severity,
            violation=violation,
            action_taken=action_taken,
            result="Intervention applied to improve antifragility",
            success=True,
        )
