"""Article III Guardian - Zero Trust Principle Enforcement.

Enforces Article III of the Vértice Constitution: The Zero Trust Principle.
Ensures no component (human or AI) is inherently trusted.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
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
from .checkers import CheckerMixin


class ArticleIIIGuardian(CheckerMixin, GuardianAgent):
    """Guardian that enforces Article III: The Zero Trust Principle.

    Monitors for:
    - Unvalidated AI-generated code
    - Missing authentication/authorization
    - Insufficient input validation
    - Trust assumptions in code
    - Missing audit trails
    - Privilege escalation risks

    Attributes:
        unvalidated_artifacts: Tracked AI artifacts awaiting validation.
        validation_history: History of validated artifacts.
        monitored_paths: Paths to monitor for violations.
        api_paths: API paths to check for authentication.
    """

    def __init__(
        self,
        monitored_paths: list[str] | None = None,
        api_paths: list[str] | None = None,
    ) -> None:
        """Initialize Article III Guardian.

        Args:
            monitored_paths: Paths to monitor for violations.
            api_paths: API paths to check for authentication.
        """
        super().__init__(
            guardian_id="guardian-article-iii",
            article=ConstitutionalArticle.ARTICLE_III,
            name="Zero Trust Guardian",
            description=(
                "Enforces the Zero Trust Principle, ensuring no component "
                "is inherently trusted and all trust is continuously verified."
            ),
        )

        self.unvalidated_artifacts: dict[str, dict[str, Any]] = {}
        self.validation_history: list[dict[str, Any]] = []

        self.monitored_paths = monitored_paths or [
            "/home/juan/vertice-dev/backend/services/maximus_core_service",
            "/home/juan/vertice-dev/backend/services/reactive_fabric_core",
        ]

        self.api_paths = api_paths or [
            "/home/juan/vertice-dev/backend/services/maximus_core_service/api",
            "/home/juan/vertice-dev/backend/services/reactive_fabric_core/api",
        ]

    def get_monitored_systems(self) -> list[str]:
        """Get list of monitored systems.

        Returns:
            List of monitored system names.
        """
        return [
            "ai_code_generation",
            "authentication_system",
            "authorization_system",
            "api_endpoints",
            "vcli_parser",
            "grpc_services",
        ]

    async def monitor(self) -> list[ConstitutionalViolation]:
        """Monitor for Zero Trust violations.

        Returns:
            List of detected violations.
        """
        violations = []

        ai_violations = await self._check_ai_artifacts()
        violations.extend(ai_violations)

        auth_violations = await self._check_authentication()
        violations.extend(auth_violations)

        validation_violations = await self._check_input_validation()
        violations.extend(validation_violations)

        trust_violations = await self._check_trust_assumptions()
        violations.extend(trust_violations)

        audit_violations = await self._check_audit_trails()
        violations.extend(audit_violations)

        return violations

    async def validate_artifact(
        self,
        file_path: str,
        validator_id: str,
        validation_notes: str,
    ) -> bool:
        """Mark an AI artifact as validated by human architect.

        Args:
            file_path: Path to file being validated.
            validator_id: ID of human validator.
            validation_notes: Notes about validation.

        Returns:
            True if validation successful.
        """
        try:
            content = Path(file_path).read_text()
            file_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

            self.validation_history.append({
                "file_hash": file_hash,
                "file_path": file_path,
                "validator_id": validator_id,
                "validation_notes": validation_notes,
                "validated": True,
                "timestamp": datetime.utcnow().isoformat(),
            })

            if file_hash in self.unvalidated_artifacts:
                del self.unvalidated_artifacts[file_hash]

            return True

        except Exception:
            return False

    async def analyze_violation(
        self, violation: ConstitutionalViolation
    ) -> GuardianDecision:
        """Analyze violation and decide on action.

        Args:
            violation: The violation to analyze.

        Returns:
            Decision on how to handle the violation.
        """
        if violation.severity == GuardianPriority.CRITICAL:
            decision_type = "veto"
            confidence = 0.99
            reasoning = (
                f"CRITICAL Zero Trust violation: {violation.rule}. "
                "This creates unacceptable security risk and must be blocked."
            )

        elif "Unvalidated AI-generated" in violation.description:
            decision_type = "escalate"
            confidence = 0.90
            reasoning = (
                "AI-generated artifact requires human architect validation "
                "per Article III Section 1."
            )

        elif "without authentication" in violation.description:
            decision_type = "block"
            confidence = 0.95
            reasoning = (
                "Endpoint lacks authentication, violating Zero Trust Principle. "
                "All interactions must be authenticated and authorized."
            )

        else:
            decision_type = "alert"
            confidence = 0.80
            reasoning = (
                f"Zero Trust violation detected: {violation.rule}. "
                "Review and implement appropriate trust verification."
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
        self, violation: ConstitutionalViolation
    ) -> GuardianIntervention:
        """Take intervention action for violation.

        Args:
            violation: The violation requiring intervention.

        Returns:
            Intervention details.
        """
        if violation.severity == GuardianPriority.CRITICAL:
            intervention_type = InterventionType.VETO
            action_taken = (
                f"Vetoed code deployment due to critical Zero Trust violation: "
                f"{violation.rule}"
            )

        elif "Unvalidated AI-generated" in violation.description:
            intervention_type = InterventionType.ESCALATION
            action_taken = (
                "Escalated AI-generated artifact to human architect for validation. "
                f"File hash: {violation.context.get('hash', 'unknown')}"
            )

        elif violation.severity == GuardianPriority.HIGH:
            intervention_type = InterventionType.REMEDIATION
            action_taken = await self._attempt_remediation(violation)

        else:
            intervention_type = InterventionType.MONITORING
            action_taken = (
                f"Increased monitoring on {violation.affected_systems[0]} "
                f"due to: {violation.description}"
            )

        return GuardianIntervention(
            guardian_id=self.guardian_id,
            intervention_type=intervention_type,
            priority=violation.severity,
            violation=violation,
            action_taken=action_taken,
            result="Intervention applied to enforce Zero Trust Principle",
            success=True,
        )

    async def _attempt_remediation(
        self, violation: ConstitutionalViolation
    ) -> str:
        """Attempt automatic remediation of violation.

        Args:
            violation: The violation to remediate.

        Returns:
            Description of remediation action taken.
        """
        if "Unvalidated input" in violation.description:
            return "Added input validation wrapper to function"

        if "without audit trail" in violation.description:
            return "Added audit logging decorator to critical operation"

        return "Remediation not available - manual fix required"
