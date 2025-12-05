"""Violation Analyzer Mixin."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..base import ConstitutionalViolation, GuardianDecision, GuardianPriority


class AnalyzerMixin:
    """Analyze violations and decide actions."""

    async def analyze_violation(self, violation: ConstitutionalViolation) -> GuardianDecision:
        """Analyze violation and decide on action."""
        from ..base import GuardianDecision, GuardianPriority
        
        # Determine decision based on severity
        if violation.severity == GuardianPriority.CRITICAL:
            decision_type = "veto"
            confidence = 0.95
            reasoning = f"CRITICAL violation of Article II {violation.clause}: {violation.rule}"
        elif violation.severity == GuardianPriority.HIGH:
            decision_type = "block"
            confidence = 0.85
            reasoning = f"HIGH severity violation of Article II {violation.clause}: {violation.rule}"
        else:
            decision_type = "alert"
            confidence = 0.75
            reasoning = f"Violation of Article II {violation.clause}: {violation.rule}"

        return GuardianDecision(
            guardian_id=self.guardian_id,
            decision_type=decision_type,
            target=violation.context.get("file", "unknown"),
            reasoning=reasoning,
            confidence=confidence,
            requires_validation=confidence < 0.9,
        )
