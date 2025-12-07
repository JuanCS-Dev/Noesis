"""Pull Request Scanner Mixin."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..base import ConstitutionalViolation


class PRScannerMixin:
    """Scan pull requests for violations."""

    async def scan_pull_request(self, pr_diff: str) -> list[ConstitutionalViolation]:
        """Scan a pull request diff for violations."""
        from ..base import ConstitutionalArticle, ConstitutionalViolation, GuardianPriority
        
        violations = []
        lines = pr_diff.splitlines()
        current_file = None
        line_number = 0

        for line in lines:
            if line.startswith("+++"):
                current_file = line[4:].strip()
                line_number = 0
                continue

            if line.startswith("@@"):
                match = re.search(r"\+(\d+)", line)
                if match:
                    line_number = int(match.group(1)) - 1
                continue

            if line.startswith("+") and not line.startswith("+++"):
                line_number += 1
                content = line[1:]

                # Check for violations in added content
                for pattern in self.mock_patterns:
                    if re.search(pattern, content):
                        violations.append(
                            ConstitutionalViolation(
                                article=ConstitutionalArticle.ARTICLE_II,
                                clause="Section 2",
                                rule="No MOCKS in production code",
                                description=f"Mock added in PR: {current_file}:{line_number}",
                                severity=GuardianPriority.HIGH,
                                evidence=[f"{current_file}:{line_number}: {content.strip()}"],
                                affected_systems=["pull_request"],
                                recommended_action="Remove mock before merging",
                                context={"file": current_file, "line": line_number, "pr_check": True},
                            )
                        )

        return violations
