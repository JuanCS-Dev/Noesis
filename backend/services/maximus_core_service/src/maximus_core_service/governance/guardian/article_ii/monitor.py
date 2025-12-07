"""Monitoring Mixin for Article II Guardian."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..base import ConstitutionalViolation


class MonitorMixin:
    """Main monitoring orchestration."""

    async def monitor(self) -> list[ConstitutionalViolation]:
        """Monitor codebase for quality standard violations."""
        violations = []

        for base_path in self.monitored_paths:
            if not os.path.exists(base_path):
                continue

            # Check Python files
            for py_file in Path(base_path).rglob("*.py"):
                # Skip excluded paths
                if any(excl in str(py_file) for excl in self.excluded_paths):
                    continue

                file_violations = await self._check_file(py_file)
                violations.extend(file_violations)

        # Check for failing tests
        test_violations = await self._check_test_health()
        violations.extend(test_violations)

        # Check git status for uncommitted mocks
        git_violations = await self._check_git_status()
        violations.extend(git_violations)

        return violations
