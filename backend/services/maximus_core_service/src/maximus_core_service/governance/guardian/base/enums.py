"""Guardian Base Enums.

Enumerations for Guardian priority levels, intervention types, and constitutional articles.
"""

from __future__ import annotations

from enum import Enum


class GuardianPriority(str, Enum):
    """Priority levels for Guardian interventions."""

    CRITICAL = "CRITICAL"  # Immediate action required
    HIGH = "HIGH"  # Urgent, within minutes
    MEDIUM = "MEDIUM"  # Important, within hours
    LOW = "LOW"  # Routine monitoring
    INFO = "INFO"  # Informational only


class InterventionType(str, Enum):
    """Types of Guardian interventions."""

    VETO = "VETO"  # Block an action completely
    ALERT = "ALERT"  # Raise awareness but don't block
    REMEDIATION = "REMEDIATION"  # Automatic fix applied
    ESCALATION = "ESCALATION"  # Escalate to human oversight
    MONITORING = "MONITORING"  # Increase monitoring level


class ConstitutionalArticle(str, Enum):
    """Constitutional Articles that Guardians enforce."""

    ARTICLE_I = "ARTICLE_I"  # Hybrid Development Cell
    ARTICLE_II = "ARTICLE_II"  # Sovereign Quality Standard
    ARTICLE_III = "ARTICLE_III"  # Zero Trust Principle
    ARTICLE_IV = "ARTICLE_IV"  # Deliberate Antifragility
    ARTICLE_V = "ARTICLE_V"  # Prior Legislation
