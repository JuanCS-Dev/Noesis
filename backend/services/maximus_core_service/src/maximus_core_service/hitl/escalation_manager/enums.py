"""
Escalation Enums.

Defines types of escalations.
"""

from __future__ import annotations

from enum import Enum


class EscalationType(Enum):
    """Type of escalation."""

    TIMEOUT = "timeout"  # SLA timeout
    HIGH_RISK = "high_risk"  # Critical/High risk decision
    MULTIPLE_REJECTIONS = "multiple_rejections"  # Rejected multiple times
    OPERATOR_REQUEST = "operator_request"  # Explicit operator escalation
    STALE_DECISION = "stale_decision"  # Decision pending too long
    SYSTEM_OVERRIDE = "system_override"  # System-initiated override
