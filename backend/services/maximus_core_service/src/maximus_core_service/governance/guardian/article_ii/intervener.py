"""Intervention Mixin."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..base import ConstitutionalViolation, GuardianIntervention, GuardianPriority


class IntervenerMixin:
    """Take intervention actions."""

    async def intervene(self, violation: ConstitutionalViolation) -> GuardianIntervention:
        """Take intervention action for violation."""
        from ..base import GuardianIntervention, GuardianPriority, InterventionType
        
        intervention_type = InterventionType.ALERT
        action_taken = ""
        success = True

        if violation.severity == GuardianPriority.CRITICAL:
            intervention_type = InterventionType.VETO
            action_taken = f"Vetoed code merge due to {violation.rule}"
        elif violation.severity == GuardianPriority.HIGH:
            intervention_type = InterventionType.ESCALATION
            action_taken = "Escalated to development team for immediate fix"
        else:
            intervention_type = InterventionType.ALERT
            action_taken = f"Created alert for: {violation.description}"

        return GuardianIntervention(
            guardian_id=self.guardian_id,
            intervention_type=intervention_type,
            priority=violation.severity,
            violation=violation,
            action_taken=action_taken,
            result=f"Intervention applied to maintain {violation.clause}",
            success=success,
        )
