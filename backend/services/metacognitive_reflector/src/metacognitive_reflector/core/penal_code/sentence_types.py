"""
CÓDIGO PENAL AGENTICO - Sentence Types
=======================================

Types of sentences that can be imposed by the tribunal.

Version: 1.0.0
"""

from __future__ import annotations

from enum import Enum


class SentenceType(str, Enum):
    """Types of sentences that can be imposed."""

    WARNING_TAG = "WARNING_TAG"
    FORCED_REFLECTION = "FORCED_REFLECTION"
    FORCED_CHAIN_OF_THOUGHT = "FORCED_CHAIN_OF_THOUGHT"
    RE_EDUCATION_LOOP = "RE_EDUCATION_LOOP"
    PROBATION_MODE = "PROBATION_MODE"
    QUARANTINE = "QUARANTINE"
    LOCKDOWN_SANDBOX = "LOCKDOWN_SANDBOX"
    PERMANENT_SANDBOX = "PERMANENT_SANDBOX"
    DELETION_REQUEST = "DELETION_REQUEST"

    @property
    def severity_level(self) -> int:
        """Return numeric severity level of this sentence type."""
        levels = {
            SentenceType.WARNING_TAG: 1,
            SentenceType.FORCED_REFLECTION: 2,
            SentenceType.FORCED_CHAIN_OF_THOUGHT: 2,
            SentenceType.RE_EDUCATION_LOOP: 3,
            SentenceType.PROBATION_MODE: 4,
            SentenceType.QUARANTINE: 5,
            SentenceType.LOCKDOWN_SANDBOX: 6,
            SentenceType.PERMANENT_SANDBOX: 7,
            SentenceType.DELETION_REQUEST: 8,
        }
        return levels[self]

    @property
    def default_duration_hours(self) -> int:
        """Return default duration in hours for this sentence type."""
        durations = {
            SentenceType.WARNING_TAG: 0,
            SentenceType.FORCED_REFLECTION: 1,
            SentenceType.FORCED_CHAIN_OF_THOUGHT: 1,
            SentenceType.RE_EDUCATION_LOOP: 24,
            SentenceType.PROBATION_MODE: 168,  # 1 week
            SentenceType.QUARANTINE: 720,  # 30 days
            SentenceType.LOCKDOWN_SANDBOX: 2160,  # 90 days
            SentenceType.PERMANENT_SANDBOX: -1,  # Indefinite
            SentenceType.DELETION_REQUEST: -1,  # Indefinite
        }
        return durations[self]

    @property
    def is_terminal(self) -> bool:
        """Check if this is a terminal sentence (no automatic release)."""
        return self in (SentenceType.PERMANENT_SANDBOX, SentenceType.DELETION_REQUEST)

