"""Checker Methods for Zero Trust Enforcement.

Mixin providing security check methods.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..base import (
    ConstitutionalArticle,
    ConstitutionalViolation,
    GuardianPriority,
)
from .patterns import (
    AI_MARKERS,
    AUDIT_PATTERNS,
    AUTH_PATTERNS,
    CRITICAL_OPERATIONS,
    DANGEROUS_PATTERNS,
    ENDPOINT_PATTERNS,
    INPUT_PATTERNS,
    VALIDATION_PATTERNS,
)

if TYPE_CHECKING:
    from .guardian import ArticleIIIGuardian


class CheckerMixin:
    """Mixin providing security checker methods.

    Provides methods for checking various security aspects:
    - AI artifact validation
    - Authentication/authorization
    - Input validation
    - Trust assumptions
    - Audit trails
    """

    # Type hints for attributes from main class
    monitored_paths: list[str]
    api_paths: list[str]
    unvalidated_artifacts: dict[str, dict[str, Any]]

    def _get_validated_hashes(self: ArticleIIIGuardian) -> set[str]:
        """Get set of validated file hashes.

        Returns:
            Set of validated file hashes.
        """
        return {
            v["file_hash"]
            for v in self.validation_history
            if v.get("validated", False)
        }

    async def _check_ai_artifacts(
        self: ArticleIIIGuardian,
    ) -> list[ConstitutionalViolation]:
        """Check for unvalidated AI-generated artifacts.

        Returns:
            List of violations for unvalidated AI code.
        """
        violations = []

        for base_path in self.monitored_paths:
            if not Path(base_path).exists():
                continue

            for py_file in Path(base_path).rglob("*.py"):
                try:
                    content = py_file.read_text()

                    for marker in AI_MARKERS:
                        if marker in content:
                            file_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

                            if file_hash not in self._get_validated_hashes():
                                violations.append(
                                    ConstitutionalViolation(
                                        article=ConstitutionalArticle.ARTICLE_III,
                                        clause="Section 1",
                                        rule="AI artifacts are untrusted until validated",
                                        description=(
                                            f"Unvalidated AI-generated code in {py_file.name}"
                                        ),
                                        severity=GuardianPriority.HIGH,
                                        evidence=[f"File contains marker: {marker}"],
                                        affected_systems=[str(py_file.parent.name)],
                                        recommended_action=(
                                            "Architect must validate AI-generated code"
                                        ),
                                        context={
                                            "file": str(py_file),
                                            "marker": marker,
                                            "hash": file_hash,
                                        },
                                    )
                                )

                                self.unvalidated_artifacts[file_hash] = {
                                    "file": str(py_file),
                                    "detected": datetime.utcnow().isoformat(),
                                    "marker": marker,
                                }

                except Exception:
                    pass

        return violations

    async def _check_authentication(
        self: ArticleIIIGuardian,
    ) -> list[ConstitutionalViolation]:
        """Check for missing authentication/authorization.

        Returns:
            List of violations for missing auth.
        """
        violations = []

        for base_path in self.api_paths:
            if not Path(base_path).exists():
                continue

            for py_file in Path(base_path).rglob("*.py"):
                try:
                    content = py_file.read_text()
                    lines = content.splitlines()

                    for i, line in enumerate(lines, 1):
                        for pattern in ENDPOINT_PATTERNS:
                            if re.search(pattern, line, re.IGNORECASE):
                                context_start = max(0, i - 5)
                                context_end = min(len(lines), i + 10)
                                context = "\n".join(lines[context_start:context_end])

                                has_auth = any(
                                    re.search(auth_pat, context, re.IGNORECASE)
                                    for auth_pat in AUTH_PATTERNS
                                )

                                if not has_auth:
                                    violations.append(
                                        ConstitutionalViolation(
                                            article=ConstitutionalArticle.ARTICLE_III,
                                            clause="Section 2",
                                            rule="All interactions are potential attack vectors",
                                            description=(
                                                f"Endpoint without authentication in "
                                                f"{py_file.name}:{i}"
                                            ),
                                            severity=GuardianPriority.CRITICAL,
                                            evidence=[f"{py_file}:{i}: {line.strip()}"],
                                            affected_systems=["api_security"],
                                            recommended_action=(
                                                "Add authentication/authorization checks"
                                            ),
                                            context={
                                                "file": str(py_file),
                                                "line": i,
                                                "endpoint": line.strip(),
                                            },
                                        )
                                    )

                except Exception:
                    pass

        return violations

    async def _check_input_validation(
        self: ArticleIIIGuardian,
    ) -> list[ConstitutionalViolation]:
        """Check for missing input validation.

        Returns:
            List of violations for unvalidated input.
        """
        violations = []

        for base_path in self.api_paths:
            if not Path(base_path).exists():
                continue

            for py_file in Path(base_path).rglob("*.py"):
                try:
                    content = py_file.read_text()
                    lines = content.splitlines()

                    for i, line in enumerate(lines, 1):
                        for pattern in INPUT_PATTERNS:
                            if re.search(pattern, line):
                                context_start = max(0, i - 2)
                                context_end = min(len(lines), i + 5)
                                context = "\n".join(lines[context_start:context_end])

                                has_validation = any(
                                    re.search(val_pat, context, re.IGNORECASE)
                                    for val_pat in VALIDATION_PATTERNS
                                )

                                if not has_validation:
                                    violations.append(
                                        ConstitutionalViolation(
                                            article=ConstitutionalArticle.ARTICLE_III,
                                            clause="Section 2",
                                            rule="User input must be validated",
                                            description=(
                                                f"Unvalidated input in {py_file.name}:{i}"
                                            ),
                                            severity=GuardianPriority.HIGH,
                                            evidence=[f"{py_file}:{i}: {line.strip()}"],
                                            affected_systems=["input_validation"],
                                            recommended_action=(
                                                "Add input validation and sanitization"
                                            ),
                                            context={
                                                "file": str(py_file),
                                                "line": i,
                                                "input_type": pattern,
                                            },
                                        )
                                    )

                except Exception:
                    pass

        return violations

    async def _check_trust_assumptions(
        self: ArticleIIIGuardian,
    ) -> list[ConstitutionalViolation]:
        """Check for dangerous trust assumptions in code.

        Returns:
            List of violations for trust assumptions.
        """
        violations = []

        for base_path in self.monitored_paths:
            if not Path(base_path).exists():
                continue

            for py_file in Path(base_path).rglob("*.py"):
                if "test" in py_file.name:
                    continue

                try:
                    content = py_file.read_text()
                    lines = content.splitlines()

                    for i, line in enumerate(lines, 1):
                        for pattern in DANGEROUS_PATTERNS:
                            if re.search(pattern, line, re.IGNORECASE):
                                violations.append(
                                    ConstitutionalViolation(
                                        article=ConstitutionalArticle.ARTICLE_III,
                                        clause="Section 1",
                                        rule="No component is inherently trustworthy",
                                        description=(
                                            f"Trust assumption in {py_file.name}:{i}"
                                        ),
                                        severity=GuardianPriority.HIGH,
                                        evidence=[f"{py_file}:{i}: {line.strip()}"],
                                        affected_systems=["trust_model"],
                                        recommended_action=(
                                            "Remove trust assumption, implement verification"
                                        ),
                                        context={
                                            "file": str(py_file),
                                            "line": i,
                                            "pattern": pattern,
                                        },
                                    )
                                )

                except Exception:
                    pass

        return violations

    async def _check_audit_trails(
        self: ArticleIIIGuardian,
    ) -> list[ConstitutionalViolation]:
        """Check for missing audit trails in critical operations.

        Returns:
            List of violations for missing audit trails.
        """
        violations = []

        for base_path in self.monitored_paths:
            if not Path(base_path).exists():
                continue

            for py_file in Path(base_path).rglob("*.py"):
                if "test" in py_file.name:
                    continue

                try:
                    content = py_file.read_text()
                    lines = content.splitlines()

                    for i, line in enumerate(lines, 1):
                        for pattern in CRITICAL_OPERATIONS:
                            if re.search(pattern, line, re.IGNORECASE):
                                context_start = max(0, i - 3)
                                context_end = min(len(lines), i + 5)
                                context = "\n".join(lines[context_start:context_end])

                                has_audit = any(
                                    re.search(audit_pat, context, re.IGNORECASE)
                                    for audit_pat in AUDIT_PATTERNS
                                )

                                if not has_audit:
                                    violations.append(
                                        ConstitutionalViolation(
                                            article=ConstitutionalArticle.ARTICLE_III,
                                            clause="Section 1",
                                            rule="Trust must be continuously verified",
                                            description=(
                                                f"Critical operation without audit trail in "
                                                f"{py_file.name}:{i}"
                                            ),
                                            severity=GuardianPriority.MEDIUM,
                                            evidence=[f"{py_file}:{i}: {line.strip()}"],
                                            affected_systems=["audit_system"],
                                            recommended_action=(
                                                "Add audit logging for this operation"
                                            ),
                                            context={
                                                "file": str(py_file),
                                                "line": i,
                                                "operation": pattern,
                                            },
                                        )
                                    )

                except Exception:
                    pass

        return violations
