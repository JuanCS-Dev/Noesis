"""Pattern Analyzer Module.

Analyzes violations for patterns, trends, and critical thresholds.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Callable, Coroutine, Any

from ..base import ConstitutionalViolation, GuardianPriority, VetoAction
from .models import CoordinatorMetrics

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class PatternAnalyzer:
    """Analyzes violation patterns and system health.

    Detects recurring issues, updates metrics, and checks
    if critical thresholds are breached.

    Attributes:
        metrics: Coordinator metrics to update.
    """

    def __init__(self, metrics: CoordinatorMetrics) -> None:
        """Initialize pattern analyzer.

        Args:
            metrics: Coordinator metrics instance.
        """
        self.metrics = metrics
        self._pattern_violation_callback: (
            Callable[[ConstitutionalViolation], Coroutine[Any, Any, None]] | None
        ) = None
        self._critical_alert_callback: (
            Callable[[ConstitutionalViolation], Coroutine[Any, Any, None]] | None
        ) = None

    def set_pattern_callback(
        self,
        callback: Callable[[ConstitutionalViolation], Coroutine[Any, Any, None]],
    ) -> None:
        """Set callback for pattern violations.

        Args:
            callback: Async function to call when pattern detected.
        """
        self._pattern_violation_callback = callback

    def set_critical_alert_callback(
        self,
        callback: Callable[[ConstitutionalViolation], Coroutine[Any, Any, None]],
    ) -> None:
        """Set callback for critical alerts.

        Args:
            callback: Async function to call for critical alerts.
        """
        self._critical_alert_callback = callback

    async def analyze_violation_patterns(
        self,
        violations: list[ConstitutionalViolation],
        time_window_hours: int = 1,
        pattern_threshold: int = 3,
    ) -> dict[str, int] | None:
        """Analyze violations for patterns and trends.

        Args:
            violations: List of all violations.
            time_window_hours: Time window for pattern detection.
            pattern_threshold: Minimum occurrences to flag as pattern.

        Returns:
            Dictionary of hot spots if patterns found, None otherwise.
        """
        if len(violations) < 10:
            return None

        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        recent_violations = [v for v in violations if v.detected_at > cutoff_time]

        patterns: dict[str, int] = defaultdict(int)

        for violation in recent_violations:
            patterns[violation.rule] += 1
            for system in violation.affected_systems:
                patterns[f"system:{system}"] += 1

        hot_spots = {k: v for k, v in patterns.items() if v >= pattern_threshold}

        if hot_spots and self._pattern_violation_callback and recent_violations:
            pattern_violation = ConstitutionalViolation(
                article=recent_violations[-1].article,
                clause="Coordinator Pattern Detection",
                rule="Repeated violations detected",
                description=f"Pattern detected: {list(hot_spots.keys())}",
                severity=GuardianPriority.HIGH,
                evidence=[f"{k}: {v} occurrences" for k, v in hot_spots.items()],
                affected_systems=["pattern_detection"],
                recommended_action="Review and address systematic issues",
            )
            await self._pattern_violation_callback(pattern_violation)

        return hot_spots if hot_spots else None

    def update_metrics(
        self,
        violations: list[ConstitutionalViolation],
    ) -> None:
        """Update coordinator metrics based on current violations.

        Args:
            violations: List of all violations.
        """
        self.metrics.violations_by_article.clear()
        self.metrics.violations_by_severity.clear()

        for violation in violations:
            article = violation.article.value
            self.metrics.violations_by_article[article] = (
                self.metrics.violations_by_article.get(article, 0) + 1
            )

            severity = violation.severity.value
            self.metrics.violations_by_severity[severity] = (
                self.metrics.violations_by_severity.get(severity, 0) + 1
            )

        self.metrics.total_violations_detected = len(violations)
        self.metrics.update_compliance_score()

    async def check_critical_thresholds(
        self,
        violations: list[ConstitutionalViolation],
        vetos: list[VetoAction],
        compliance_threshold: float = 80.0,
        veto_threshold: int = 5,
    ) -> list[ConstitutionalViolation]:
        """Check if critical thresholds are breached.

        Args:
            violations: List of all violations.
            vetos: List of all vetos.
            compliance_threshold: Minimum acceptable compliance score.
            veto_threshold: Maximum acceptable vetos per hour.

        Returns:
            List of critical violations generated.
        """
        critical_violations = []

        if self.metrics.compliance_score < compliance_threshold:
            article = violations[-1].article if violations else None
            violation = ConstitutionalViolation(
                article=article,
                clause="System Compliance",
                rule="Compliance below threshold",
                description=(
                    f"System compliance at {self.metrics.compliance_score:.1f}%"
                ),
                severity=GuardianPriority.CRITICAL,
                evidence=[f"Compliance score below {compliance_threshold}%"],
                affected_systems=["entire_ecosystem"],
                recommended_action="Emergency review required",
            )
            critical_violations.append(violation)
            if self._critical_alert_callback:
                await self._critical_alert_callback(violation)

        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        recent_vetos = [v for v in vetos if v.enacted_at > cutoff_time]

        if len(recent_vetos) > veto_threshold:
            article = violations[-1].article if violations else None
            violation = ConstitutionalViolation(
                article=article,
                clause="Veto Threshold",
                rule="Excessive vetos",
                description=f"{len(recent_vetos)} vetos in past hour",
                severity=GuardianPriority.CRITICAL,
                evidence=[f"Veto IDs: {[v.veto_id for v in recent_vetos[:3]]}"],
                affected_systems=["veto_system"],
                recommended_action="Human intervention required",
            )
            critical_violations.append(violation)
            if self._critical_alert_callback:
                await self._critical_alert_callback(violation)

        return critical_violations
