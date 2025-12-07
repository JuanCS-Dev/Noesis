"""Article IV Antifragility Checkers.

Monitoring methods for chaos engineering, resilience, and fragility detection.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ..base import ConstitutionalArticle, ConstitutionalViolation, GuardianPriority


class AntifragilityCheckerMixin:
    """Mixin providing antifragility check methods.

    Contains all monitoring checks for Article IV compliance:
    - Chaos engineering tests
    - Resilience patterns
    - Experimental features
    - Failure recovery
    - System fragility

    Attributes:
        test_paths: Paths to check for tests.
        service_paths: Paths to check for services.
        resilience_patterns: Patterns to detect.
        chaos_indicators: Indicators of chaos tests.
        chaos_experiments: List of experiments.
        quarantined_features: Dict of quarantined features.
    """

    test_paths: list[str]
    service_paths: list[str]
    resilience_patterns: list[str]
    chaos_indicators: list[str]
    chaos_experiments: list[dict[str, Any]]
    quarantined_features: dict[str, dict[str, Any]]

    async def _check_chaos_engineering(self) -> list[ConstitutionalViolation]:
        """Check for presence of chaos engineering tests.

        Returns:
            List of violations related to insufficient chaos testing.
        """
        violations = []

        for base_path in self.test_paths:
            if not Path(base_path).exists():
                continue

            chaos_test_count = 0
            regular_test_count = 0

            for test_file in Path(base_path).rglob("test_*.py"):
                try:
                    content = test_file.read_text(encoding="utf-8")
                    has_chaos = any(
                        indicator in content.lower()
                        for indicator in self.chaos_indicators
                    )

                    if has_chaos:
                        chaos_test_count += 1
                    else:
                        regular_test_count += 1
                except OSError:
                    pass

            if regular_test_count > 0:
                chaos_ratio = chaos_test_count / (chaos_test_count + regular_test_count)

                if chaos_ratio < 0.1:
                    violations.append(
                        ConstitutionalViolation(
                            article=ConstitutionalArticle.ARTICLE_IV,
                            clause="Section 1",
                            rule="Must anticipate and provoke failures",
                            description=(
                                f"Insufficient chaos testing in {Path(base_path).name}"
                            ),
                            severity=GuardianPriority.MEDIUM,
                            evidence=[
                                f"Chaos test ratio: {chaos_ratio:.1%}",
                                f"Found {chaos_test_count} chaos tests out of "
                                f"{regular_test_count + chaos_test_count} total",
                            ],
                            affected_systems=[Path(base_path).name],
                            recommended_action="Add more chaos engineering tests",
                            context={
                                "path": str(base_path),
                                "chaos_tests": chaos_test_count,
                                "total_tests": regular_test_count + chaos_test_count,
                            },
                        )
                    )

        recent_experiments = [
            exp for exp in self.chaos_experiments
            if datetime.fromisoformat(exp["timestamp"]) > datetime.utcnow() - timedelta(days=7)
        ]

        if len(recent_experiments) < 3:
            violations.append(
                ConstitutionalViolation(
                    article=ConstitutionalArticle.ARTICLE_IV,
                    clause="Section 1",
                    rule="Controlled failures must be regularly provoked",
                    description="Insufficient chaos experiments in past week",
                    severity=GuardianPriority.MEDIUM,
                    evidence=[f"Only {len(recent_experiments)} experiments in past 7 days"],
                    affected_systems=["chaos_engineering"],
                    recommended_action="Schedule and run chaos experiments",
                    context={"recent_count": len(recent_experiments)},
                )
            )

        return violations

    async def _check_resilience_patterns(self) -> list[ConstitutionalViolation]:
        """Check for implementation of resilience patterns.

        Returns:
            List of violations for missing resilience patterns.
        """
        violations = []

        for base_path in self.service_paths:
            if not Path(base_path).exists():
                continue

            pattern_counts = {pattern: 0 for pattern in self.resilience_patterns}

            for py_file in Path(base_path).rglob("*.py"):
                if "test" in py_file.name:
                    continue

                try:
                    content = py_file.read_text(encoding="utf-8").lower()

                    for pattern in self.resilience_patterns:
                        if pattern.replace("_", " ") in content or pattern in content:
                            pattern_counts[pattern] += 1
                except OSError:
                    pass

            missing_patterns = [p for p, count in pattern_counts.items() if count == 0]

            if len(missing_patterns) > 3:
                violations.append(
                    ConstitutionalViolation(
                        article=ConstitutionalArticle.ARTICLE_IV,
                        clause="Section 1",
                        rule="System must be antifragile",
                        description=f"Missing resilience patterns in {Path(base_path).name}",
                        severity=GuardianPriority.HIGH,
                        evidence=[
                            f"Missing patterns: {', '.join(missing_patterns[:5])}",
                            f"Total missing: {len(missing_patterns)} "
                            f"out of {len(self.resilience_patterns)}",
                        ],
                        affected_systems=[Path(base_path).name],
                        recommended_action=(
                            "Implement circuit breakers, retries, and fallback mechanisms"
                        ),
                        context={
                            "path": str(base_path),
                            "missing": missing_patterns,
                            "found": {p: c for p, c in pattern_counts.items() if c > 0},
                        },
                    )
                )

        return violations

    async def _check_experimental_features(self) -> list[ConstitutionalViolation]:
        """Check for experimental features without proper quarantine.

        Returns:
            List of violations for unquarantined experimental features.
        """
        violations = []

        experimental_markers = [
            "@experimental",
            "@beta",
            "EXPERIMENTAL",
            "BETA",
            "alpha_feature",
            "unstable",
            "preview",
        ]

        for base_path in self.service_paths:
            if not Path(base_path).exists():
                continue

            for py_file in Path(base_path).rglob("*.py"):
                try:
                    content = py_file.read_text(encoding="utf-8")

                    for marker in experimental_markers:
                        if marker in content:
                            feature_id = f"{py_file.name}_{marker}"

                            if feature_id not in self.quarantined_features:
                                violations.append(
                                    ConstitutionalViolation(
                                        article=ConstitutionalArticle.ARTICLE_IV,
                                        clause="Section 2",
                                        rule="High-risk ideas require quarantine validation",
                                        description=(
                                            f"Experimental feature without quarantine "
                                            f"in {py_file.name}"
                                        ),
                                        severity=GuardianPriority.HIGH,
                                        evidence=[f"Found marker: {marker}"],
                                        affected_systems=[str(py_file.parent.name)],
                                        recommended_action=(
                                            "Move to quarantined repository for validation"
                                        ),
                                        context={
                                            "file": str(py_file),
                                            "marker": marker,
                                            "feature_id": feature_id,
                                        },
                                    )
                                )
                            else:
                                quarantine = self.quarantined_features[feature_id]
                                if quarantine.get("status") != "validated":
                                    days_in_quarantine = (
                                        datetime.utcnow() -
                                        datetime.fromisoformat(quarantine["quarantine_start"])
                                    ).days

                                    if days_in_quarantine > 30:
                                        violations.append(
                                            ConstitutionalViolation(
                                                article=ConstitutionalArticle.ARTICLE_IV,
                                                clause="Section 2",
                                                rule="Quarantined features require validation",
                                                description=(
                                                    f"Feature in quarantine too long: "
                                                    f"{feature_id}"
                                                ),
                                                severity=GuardianPriority.MEDIUM,
                                                evidence=[
                                                    f"In quarantine for {days_in_quarantine} days"
                                                ],
                                                affected_systems=["experimental_features"],
                                                recommended_action=(
                                                    "Complete public validation or remove feature"
                                                ),
                                                context={
                                                    "feature_id": feature_id,
                                                    "days": days_in_quarantine,
                                                },
                                            )
                                        )
                except OSError:
                    pass

        return violations

    async def _check_failure_recovery(self) -> list[ConstitutionalViolation]:
        """Check for proper failure recovery mechanisms.

        Returns:
            List of violations for missing recovery mechanisms.
        """
        violations = []

        recovery_patterns = [
            r"try:\s*\n.*\nexcept",
            r"with.*suppress",
            r"finally:",
            r"on_error",
            r"handle_failure",
            r"recover",
            r"rollback",
        ]

        critical_operations = [
            "database",
            "transaction",
            "payment",
            "authentication",
            "critical",
        ]

        for base_path in self.service_paths:
            if not Path(base_path).exists():
                continue

            for py_file in Path(base_path).rglob("*.py"):
                if "test" in py_file.name:
                    continue

                try:
                    content = py_file.read_text(encoding="utf-8")
                    lower_content = content.lower()

                    has_critical = any(op in lower_content for op in critical_operations)

                    if has_critical:
                        has_recovery = any(
                            re.search(pattern, content)
                            for pattern in recovery_patterns
                        )

                        if not has_recovery:
                            violations.append(
                                ConstitutionalViolation(
                                    article=ConstitutionalArticle.ARTICLE_IV,
                                    clause="Section 1",
                                    rule="System must recover from failures",
                                    description=(
                                        f"Critical operations without recovery "
                                        f"in {py_file.name}"
                                    ),
                                    severity=GuardianPriority.HIGH,
                                    evidence=[
                                        "Missing error recovery for critical operations"
                                    ],
                                    affected_systems=[str(py_file.parent.name)],
                                    recommended_action=(
                                        "Add proper error handling and recovery"
                                    ),
                                    context={"file": str(py_file)},
                                )
                            )
                except OSError:
                    pass

        return violations

    async def _check_system_fragility(self) -> list[ConstitutionalViolation]:
        """Check for indicators of system fragility.

        Returns:
            List of violations indicating system fragility.
        """
        violations = []

        fragility_indicators = {
            "single_points_of_failure": 0,
            "hardcoded_values": 0,
            "global_state": 0,
            "tight_coupling": 0,
            "missing_timeouts": 0,
        }

        for base_path in self.service_paths:
            if not Path(base_path).exists():
                continue

            for py_file in Path(base_path).rglob("*.py"):
                if "test" in py_file.name:
                    continue

                try:
                    content = py_file.read_text(encoding="utf-8")

                    if "singleton" in content.lower():
                        fragility_indicators["single_points_of_failure"] += 1

                    if re.search(r'["\']https?://[^"\']+["\']', content):
                        fragility_indicators["hardcoded_values"] += 1

                    if "global" in content:
                        fragility_indicators["global_state"] += 1

                    if "timeout" not in content.lower() and any(
                        x in content.lower() for x in ["request", "connect", "socket"]
                    ):
                        fragility_indicators["missing_timeouts"] += 1
                except OSError:
                    pass

        total_fragility = sum(fragility_indicators.values())

        if total_fragility > 10:
            violations.append(
                ConstitutionalViolation(
                    article=ConstitutionalArticle.ARTICLE_IV,
                    clause="Section 1",
                    rule="System must be antifragile not fragile",
                    description="High system fragility detected",
                    severity=GuardianPriority.HIGH,
                    evidence=[
                        f"Fragility score: {total_fragility}",
                        f"Single points of failure: "
                        f"{fragility_indicators['single_points_of_failure']}",
                        f"Hardcoded values: {fragility_indicators['hardcoded_values']}",
                        f"Missing timeouts: {fragility_indicators['missing_timeouts']}",
                    ],
                    affected_systems=["system_architecture"],
                    recommended_action=(
                        "Refactor to reduce fragility and increase resilience"
                    ),
                    context=fragility_indicators,
                )
            )

        return violations
