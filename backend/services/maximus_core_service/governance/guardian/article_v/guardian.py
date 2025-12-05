"""Article V Guardian - Prior Legislation Enforcement.

Main guardian class for Article V enforcement.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-13
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
from .checkers import (
    check_autonomous_governance,
    check_hitl_controls,
    check_kill_switches,
    check_responsibility_doctrine,
    check_two_man_rule,
)
from .config import (
    AUTONOMOUS_INDICATORS,
    DEFAULT_AUTONOMOUS_PATHS,
    DEFAULT_GOVERNANCE_PATHS,
    DEFAULT_HITL_PATHS,
    DEFAULT_POWERFUL_PATHS,
    DEFAULT_PROCESS_PATHS,
    GOVERNANCE_INDICATORS,
    RESPONSIBILITY_REQUIREMENTS,
)
from .registry import register_governance, validate_governance_precedence


class ArticleVGuardian(GuardianAgent):
    """Guardian that enforces Article V: Prior Legislation Principle.

    Monitors for:
    - Autonomous capabilities without governance
    - Missing responsibility chains
    - Absence of HITL controls for critical operations
    - Unaudited autonomous workflows
    - Missing kill switches and safety mechanisms
    - Violations of Two-Man Rule for critical actions
    """

    def __init__(
        self,
        autonomous_paths: list[str] | None = None,
        powerful_paths: list[str] | None = None,
        hitl_paths: list[str] | None = None,
        process_paths: list[str] | None = None,
        governance_paths: list[str] | None = None,
    ):
        """Initialize Article V Guardian.

        Args:
            autonomous_paths: Paths to check for autonomous systems
            powerful_paths: Paths to check for powerful operations
            hitl_paths: Paths to check for HITL controls
            process_paths: Paths to check for long-running processes
            governance_paths: Paths to check for Two-Man Rule
        """
        super().__init__(
            guardian_id="guardian-article-v",
            article=ConstitutionalArticle.ARTICLE_V,
            name="Prior Legislation Guardian",
            description=(
                "Enforces the Prior Legislation Principle, ensuring governance "
                "is implemented before autonomous systems of power."
            ),
        )

        self.autonomous_systems: dict[str, dict[str, Any]] = {}
        self.governance_registry: dict[str, dict[str, Any]] = {}

        # Configurable paths
        self.autonomous_paths = autonomous_paths or DEFAULT_AUTONOMOUS_PATHS
        self.powerful_paths = powerful_paths or DEFAULT_POWERFUL_PATHS
        self.hitl_paths = hitl_paths or DEFAULT_HITL_PATHS
        self.process_paths = process_paths or DEFAULT_PROCESS_PATHS
        self.governance_paths = governance_paths or DEFAULT_GOVERNANCE_PATHS

    @property
    def responsibility_requirements(self) -> list[str]:
        """Get responsibility requirements (backward compat)."""
        return RESPONSIBILITY_REQUIREMENTS

    @property
    def autonomous_indicators(self) -> list[str]:
        """Get autonomous indicators (backward compat)."""
        return AUTONOMOUS_INDICATORS

    @property
    def governance_indicators(self) -> list[str]:
        """Get governance indicators (backward compat)."""
        return GOVERNANCE_INDICATORS

    async def _check_autonomous_governance(
        self,
        paths: list[str] | None = None,
    ) -> list[ConstitutionalViolation]:
        """Check for autonomous governance (backward compat wrapper)."""
        return await check_autonomous_governance(
            paths or self.autonomous_paths, self.autonomous_systems
        )

    async def _check_responsibility_doctrine(
        self,
        paths: list[str] | None = None,
    ) -> list[ConstitutionalViolation]:
        """Check responsibility doctrine (backward compat wrapper)."""
        return await check_responsibility_doctrine(paths or self.powerful_paths)

    async def _check_hitl_controls(
        self,
        paths: list[str] | None = None,
    ) -> list[ConstitutionalViolation]:
        """Check HITL controls (backward compat wrapper)."""
        return await check_hitl_controls(paths or self.hitl_paths)

    async def _check_kill_switches(
        self,
        paths: list[str] | None = None,
    ) -> list[ConstitutionalViolation]:
        """Check kill switches (backward compat wrapper)."""
        return await check_kill_switches(paths or self.process_paths)

    async def _check_two_man_rule(
        self,
        paths: list[str] | None = None,
    ) -> list[ConstitutionalViolation]:
        """Check Two-Man Rule (backward compat wrapper)."""
        return await check_two_man_rule(paths or self.governance_paths)

    def get_monitored_systems(self) -> list[str]:
        """Get list of monitored systems."""
        return [
            "autonomous_agents",
            "governance_framework",
            "responsibility_chain",
            "hitl_controls",
            "audit_system",
            "safety_mechanisms",
        ]

    async def monitor(self) -> list[ConstitutionalViolation]:
        """Monitor for Prior Legislation violations.

        Returns:
            List of detected violations
        """
        violations = []

        autonomous_violations = await self._check_autonomous_governance()
        violations.extend(autonomous_violations)

        responsibility_violations = await self._check_responsibility_doctrine()
        violations.extend(responsibility_violations)

        hitl_violations = await self._check_hitl_controls()
        violations.extend(hitl_violations)

        killswitch_violations = await self._check_kill_switches()
        violations.extend(killswitch_violations)

        twoman_violations = await self._check_two_man_rule()
        violations.extend(twoman_violations)

        return violations

    async def register_governance(
        self,
        system_id: str,
        governance_type: str,
        policies: list[str],
        controls: dict[str, Any],
    ) -> bool:
        """Register governance for an autonomous system.

        Args:
            system_id: Identifier of the autonomous system
            governance_type: Type of governance applied
            policies: List of applicable policies
            controls: Control mechanisms in place

        Returns:
            True if registration successful
        """
        return await register_governance(
            self.governance_registry,
            self.autonomous_systems,
            system_id,
            governance_type,
            policies,
            controls,
        )

    async def validate_governance_precedence(
        self,
        system_path: str,
    ) -> tuple[bool, str]:
        """Validate that governance was implemented before autonomy.

        Args:
            system_path: Path to the autonomous system

        Returns:
            Tuple of (is_valid, reason)
        """
        return await validate_governance_precedence(system_path)

    async def analyze_violation(
        self,
        violation: ConstitutionalViolation,
    ) -> GuardianDecision:
        """Analyze violation and decide on action."""
        if violation.severity == GuardianPriority.CRITICAL:
            decision_type = "veto"
            confidence = 0.98
            reasoning = (
                f"CRITICAL violation of Prior Legislation: {violation.rule}. "
                "Autonomous power without governance is forbidden."
            )

        elif "without governance" in violation.description:
            decision_type = "block"
            confidence = 0.95
            reasoning = (
                "Autonomous capability detected without governance framework. "
                "Article V requires governance before autonomy."
            )

        elif "Two-Man Rule" in violation.rule:
            decision_type = "escalate"
            confidence = 0.90
            reasoning = (
                "Critical action lacks dual approval mechanism. "
                "Responsibility Doctrine requires Two-Man Rule."
            )

        elif "kill switch" in violation.description.lower():
            decision_type = "block"
            confidence = 0.92
            reasoning = (
                "Autonomous system lacks emergency stop capability. "
                "This violates OPSEC requirements in Anexo C."
            )

        else:
            decision_type = "alert"
            confidence = 0.80
            reasoning = (
                f"Prior Legislation violation: {violation.rule}. "
                "Governance controls need strengthening."
            )

        return GuardianDecision(
            guardian_id=self.guardian_id,
            decision_type=decision_type,
            target=violation.context.get("file", "unknown"),
            reasoning=reasoning,
            confidence=confidence,
            requires_validation=decision_type == "escalate",
        )

    async def intervene(
        self,
        violation: ConstitutionalViolation,
    ) -> GuardianIntervention:
        """Take intervention action for violation."""
        if violation.severity == GuardianPriority.CRITICAL:
            intervention_type = InterventionType.VETO
            action_taken = (
                "Vetoed autonomous capability activation. "
                "Governance must be implemented first."
            )

            if "system_id" in violation.context:
                self.autonomous_systems[violation.context["system_id"]][
                    "disabled"
                ] = True

        elif "without governance" in violation.description:
            intervention_type = InterventionType.REMEDIATION
            action_taken = (
                "Generated governance template for autonomous system. "
                "System blocked until governance implemented."
            )

        elif "HITL" in violation.description:
            intervention_type = InterventionType.ESCALATION
            action_taken = (
                "Escalated to add Human-In-The-Loop control. "
                "Critical operation requires human oversight."
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
            result="Intervention applied to enforce Prior Legislation",
            success=True,
        )
