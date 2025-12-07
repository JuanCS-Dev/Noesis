"""
Helper Methods for Article II Guardian.

Utility methods for validation and analysis.
"""

from __future__ import annotations

import re


class HelperMethodsMixin:
    """Helper methods for Article II Guardian."""

    def _is_comment_or_string(self, line: str, pattern: str) -> bool:
        """Check if pattern match is in comment or string literal."""
        # Remove strings first
        line_no_strings = re.sub(r'["\'].*?["\']', "", line)
        
        # Check if in comment
        if "#" in line_no_strings:
            comment_pos = line_no_strings.index("#")
            match = re.search(pattern, line)
            if match and match.start() > comment_pos:
                return True
        
        # Check if original match was in a string
        if re.search(pattern, line) and not re.search(pattern, line_no_strings):
            return True
        
        return False

    def _has_valid_skip_reason(self, lines: list[str], line_num: int) -> bool:
        """Check if skipped test has valid reason comment."""
        # Check previous 3 lines for skip reason
        start = max(0, line_num - 4)
        for prev_line in lines[start:line_num]:
            if "future:" in prev_line.lower() or "roadmap" in prev_line.lower():
                return True
        return False

    def get_monitored_systems(self) -> list[str]:
        """Get list of monitored systems."""
        return [
            "maximus_core_service",
            "reactive_fabric_core",
            "active_immune_core",
            "governance_module",
        ]
