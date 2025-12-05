"""Git Status Checker Mixin."""

from __future__ import annotations

import os
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..base import ConstitutionalViolation


class GitCheckerMixin:
    """Check git status for violations."""

    async def _check_git_status(self) -> list[ConstitutionalViolation]:
        """Check git status for uncommitted mocks."""
        violations = []
        # Could check git diff for mock patterns
        return violations
