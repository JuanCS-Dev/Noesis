"""
File Checker Mixin for Article II Guardian.

Checks individual files for quality violations.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..base import ConstitutionalViolation


class FileCheckerMixin:
    """Mixin for checking individual files."""

    async def _check_file(self, file_path: Path) -> list[ConstitutionalViolation]:
        """Check a single file for violations."""
        from ..base import ConstitutionalArticle, ConstitutionalViolation, GuardianPriority

        violations = []

        try:
            content = file_path.read_text()
            lines = content.splitlines()

            # Check for mock implementations
            for i, line in enumerate(lines, 1):
                # Check mock patterns
                for pattern in self.mock_patterns:
                    if re.search(pattern, line):
                        # Verify it's not in a comment or string
                        if not self._is_comment_or_string(line, pattern):
                            violations.append(
                                ConstitutionalViolation(
                                    article=ConstitutionalArticle.ARTICLE_II,
                                    clause="Section 2",
                                    rule="No MOCKS in production code",
                                    description=f"Mock implementation found in {file_path.name}:{i}",
                                    severity=GuardianPriority.HIGH,
                                    evidence=[f"{file_path}:{i}: {line.strip()}"],
                                    affected_systems=[str(file_path.parent.name)],
                                    recommended_action="Replace mock with real implementation",
                                    context={"file": str(file_path), "line": i, "pattern": pattern},
                                )
                            )

                # Check placeholder patterns
                for pattern in self.placeholder_patterns:
                    if re.search(pattern, line):
                        violations.append(
                            ConstitutionalViolation(
                                article=ConstitutionalArticle.ARTICLE_II,
                                clause="Section 2",
                                rule="No PLACEHOLDERS or TODOs in production",
                                description=f"Placeholder/TODO found in {file_path.name}:{i}",
                                severity=GuardianPriority.MEDIUM,
                                evidence=[f"{file_path}:{i}: {line.strip()}"],
                                affected_systems=[str(file_path.parent.name)],
                                recommended_action="Complete implementation or move to feature branch",
                                context={"file": str(file_path), "line": i, "pattern": pattern},
                            )
                        )

            # Check for skipped tests (if it's a test file)
            if "test" in file_path.name.lower():
                violations.extend(self._check_skipped_tests(file_path, lines))

            # Check for NotImplementedError
            violations.extend(self._check_not_implemented(file_path, content))

        except Exception:
            # Error reading file - note but don't crash
            pass

        return violations

    def _check_skipped_tests(self, file_path: Path, lines: list[str]) -> list[ConstitutionalViolation]:
        """Check for skipped tests in test files."""
        from ..base import ConstitutionalArticle, ConstitutionalViolation, GuardianPriority

        violations = []
        for i, line in enumerate(lines, 1):
            for pattern in self.test_skip_patterns:
                if re.search(pattern, line):
                    # Check if there's a valid reason
                    if not self._has_valid_skip_reason(lines, i):
                        violations.append(
                            ConstitutionalViolation(
                                article=ConstitutionalArticle.ARTICLE_II,
                                clause="Section 3",
                                rule="No skipped tests without future dependency",
                                description=f"Skipped test without valid reason in {file_path.name}:{i}",
                                severity=GuardianPriority.MEDIUM,
                                evidence=[f"{file_path}:{i}: {line.strip()}"],
                                affected_systems=["test_suite"],
                                recommended_action="Fix test or document future dependency in ROADMAP",
                                context={"file": str(file_path), "line": i},
                            )
                        )
        return violations

    def _check_not_implemented(self, file_path: Path, content: str) -> list[ConstitutionalViolation]:
        """Check for NotImplementedError in code."""
        from ..base import ConstitutionalArticle, ConstitutionalViolation, GuardianPriority

        violations = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Raise):
                    if (
                        isinstance(node.exc, ast.Call)
                        and isinstance(node.exc.func, ast.Name)
                        and node.exc.func.id == "NotImplementedError"
                    ):
                        violations.append(
                            ConstitutionalViolation(
                                article=ConstitutionalArticle.ARTICLE_II,
                                clause="Section 1",
                                rule="Code must be PRODUCTION-READY",
                                description=f"NotImplementedError in {file_path.name}",
                                severity=GuardianPriority.CRITICAL,
                                evidence=[f"{file_path}: NotImplementedError found"],
                                affected_systems=[str(file_path.parent.name)],
                                recommended_action="Implement the functionality",
                                context={"file": str(file_path)},
                            )
                        )
        except SyntaxError:
            # File has syntax errors - also a violation!
            violations.append(
                ConstitutionalViolation(
                    article=ConstitutionalArticle.ARTICLE_II,
                    clause="Section 1",
                    rule="Code must be PRODUCTION-READY",
                    description=f"Syntax error in {file_path.name}",
                    severity=GuardianPriority.CRITICAL,
                    evidence=[f"{file_path}: Syntax error detected"],
                    affected_systems=[str(file_path.parent.name)],
                    recommended_action="Fix syntax errors",
                    context={"file": str(file_path)},
                )
            )

        return violations
