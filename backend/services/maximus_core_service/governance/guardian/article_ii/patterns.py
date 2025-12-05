"""
Article II Guardian Patterns.

Detection patterns for quality violations.
"""

from __future__ import annotations


class GuardianPatterns:
    """Patterns for detecting quality violations."""

    mock_patterns = [
        r"\bmock\b",
        r"\bMock\b",
        r"\bfake\b",
        r"\bFake\b",
        r"\bstub\b",
        r"\bStub\b",
        r"\bdummy\b",
        r"\bDummy\b",
    ]

    placeholder_patterns = [
        r"\bTODO\b",
        r"\bFIXME\b",
        r"\bHACK\b",
        r"\bXXX\b",
        r"\bTEMP\b",
        r"\bplaceholder\b",
        r"NotImplementedError",
        r"raise NotImplemented",
        r"pass\s*#.*implement",
    ]

    test_skip_patterns = [
        r"@pytest\.mark\.skip",
        r"@unittest\.skip",
        r"\.skip\(",
        r"skipTest\(",
        r"@skip",
    ]

    monitored_paths = [
        "/home/juan/vertice-dev/backend/services/maximus_core_service",
        "/home/juan/vertice-dev/backend/services/reactive_fabric_core",
        "/home/juan/vertice-dev/backend/services/active_immune_core",
    ]

    excluded_paths = [
        "test_",
        "_test.py",
        "/tests/",
        "/test/",
        "__pycache__",
        ".git",
        "/migrations/",
        "/docs/",
    ]
