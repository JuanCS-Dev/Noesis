"""Conflict Resolution Module.

Handles detection and resolution of conflicts between Guardian decisions.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from ..base import ConstitutionalViolation, GuardianPriority
from .models import ConflictResolution

if TYPE_CHECKING:
    pass


class ConflictResolver:
    """Resolves conflicts between Guardian decisions.

    When multiple Guardians detect violations on the same target,
    this resolver determines which violation takes precedence.

    Attributes:
        conflict_resolutions: List of resolved conflicts.
    """

    def __init__(self) -> None:
        """Initialize conflict resolver."""
        self.conflict_resolutions: list[ConflictResolution] = []

    def resolve_conflicts(
        self,
        violations: list[ConstitutionalViolation],
        time_window_minutes: int = 5,
    ) -> list[ConflictResolution]:
        """Resolve conflicts between Guardian decisions.

        Args:
            violations: List of all violations.
            time_window_minutes: Time window for considering violations.

        Returns:
            List of new conflict resolutions.
        """
        violations_by_target = defaultdict(list)
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)

        recent_violations = [
            v for v in violations if v.detected_at > cutoff_time
        ]

        for violation in recent_violations:
            target = violation.context.get("file", "unknown")
            violations_by_target[target].append(violation)

        new_resolutions = []
        for target, target_violations in violations_by_target.items():
            if len(target_violations) > 1:
                resolutions = self._resolve_target_conflicts(target_violations)
                new_resolutions.extend(resolutions)

        self.conflict_resolutions.extend(new_resolutions)
        return new_resolutions

    def _resolve_target_conflicts(
        self,
        violations: list[ConstitutionalViolation],
    ) -> list[ConflictResolution]:
        """Resolve conflicts for violations on same target.

        Args:
            violations: Violations on the same target.

        Returns:
            List of conflict resolutions.
        """
        violations.sort(
            key=lambda v: (
                self._get_severity_priority(v.severity),
                self._get_article_precedence(v.article.value),
            )
        )

        primary = violations[0]
        resolutions = []

        for secondary in violations[1:]:
            if self._is_conflicting(primary, secondary):
                resolution = ConflictResolution(
                    conflict_id=f"conflict_{datetime.utcnow().timestamp()}",
                    guardian1_id=f"guardian-{primary.article.value.lower()}",
                    guardian2_id=f"guardian-{secondary.article.value.lower()}",
                    violation1=primary,
                    violation2=secondary,
                    resolution=(
                        f"Prioritized {primary.article.value} "
                        f"over {secondary.article.value}"
                    ),
                    rationale=(
                        f"Higher severity ({primary.severity.value}) "
                        f"and article precedence"
                    ),
                )
                resolutions.append(resolution)

        return resolutions

    def _is_conflicting(
        self,
        v1: ConstitutionalViolation,
        v2: ConstitutionalViolation,
    ) -> bool:
        """Check if two violations conflict.

        Args:
            v1: First violation.
            v2: Second violation.

        Returns:
            True if violations recommend opposite actions.
        """
        if v1.recommended_action == v2.recommended_action:
            return False

        action1_lower = v1.recommended_action.lower()
        action2_lower = v2.recommended_action.lower()

        if "allow" in action1_lower and "block" in action2_lower:
            return True
        if "block" in action1_lower and "allow" in action2_lower:
            return True

        return False

    def _get_severity_priority(self, severity: GuardianPriority) -> int:
        """Get numeric priority for severity.

        Args:
            severity: Guardian priority level.

        Returns:
            Numeric priority (lower = higher priority).
        """
        priorities = {
            GuardianPriority.CRITICAL: 0,
            GuardianPriority.HIGH: 1,
            GuardianPriority.MEDIUM: 2,
            GuardianPriority.LOW: 3,
            GuardianPriority.INFO: 4,
        }
        return priorities.get(severity, 5)

    def _get_article_precedence(self, article: str) -> int:
        """Get precedence order for articles.

        Article V (Prior Legislation) has highest precedence,
        followed by Article III (Zero Trust), Article II (Quality),
        and Article IV (Antifragility).

        Args:
            article: Article identifier.

        Returns:
            Numeric precedence (lower = higher priority).
        """
        precedence = {
            "ARTICLE_V": 0,
            "ARTICLE_III": 1,
            "ARTICLE_II": 2,
            "ARTICLE_IV": 3,
            "ARTICLE_I": 4,
        }
        return precedence.get(article, 5)
