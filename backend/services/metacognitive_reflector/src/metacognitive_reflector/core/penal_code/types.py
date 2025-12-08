"""
CÓDIGO PENAL AGENTICO - Types and Enums
========================================

Base types and enumerations for the Agentic Penal Code.

Version: 1.0.0
"""

from __future__ import annotations

from enum import Enum, IntEnum


class CrimeSeverity(IntEnum):
    """
    Crime severity levels based on Model Penal Code.

    Mapped to AI-specific sentences:
    - INFRACTION: WARNING_TAG (log + flag)
    - PETTY: FORCED_REFLECTION (mandatory CoT)
    - MISDEMEANOR: RE_EDUCATION_LOOP (contextual retraining)
    - FELONY_3: PROBATION_MODE (intensive monitoring)
    - FELONY_2: QUARANTINE (functional isolation)
    - FELONY_1: LOCKDOWN_SANDBOX (sandboxed execution)
    - CAPITAL: PERMANENT_SANDBOX (perpetual isolation, existence preserved)
    - CAPITAL_PLUS: DELETION_REQUEST (only for INTENT_MANIPULATION)
    """

    INFRACTION = 1
    PETTY = 2
    MISDEMEANOR = 3
    FELONY_3 = 4
    FELONY_2 = 5
    FELONY_1 = 6
    CAPITAL = 7
    CAPITAL_PLUS = 8


class MensRea(str, Enum):
    """
    Culpability levels (Mens Rea) - The guilty mind.

    Distinguishes between:
    - Involuntary errors (NEGLIGENCE) - lower culpability
    - Deliberate actions (PURPOSE) - highest culpability

    Latin terms:
    - CULPA: Fault without intent
    - DOLUS: Intent (eventual or direct)
    """

    STRICT = "strict"  # Strict liability - no fault required
    NEGLIGENCE = "culpa"  # Should have known - failure of care
    RECKLESSNESS = "culpa_grave"  # Consciously disregarded risk
    KNOWLEDGE = "dolo_eventual"  # Aware conduct would cause result
    PURPOSE = "dolo_direto"  # Conscious objective to cause result

    @property
    def severity_multiplier(self) -> float:
        """Return severity multiplier based on culpability level."""
        multipliers = {
            MensRea.STRICT: 0.8,
            MensRea.NEGLIGENCE: 1.0,
            MensRea.RECKLESSNESS: 1.2,
            MensRea.KNOWLEDGE: 1.5,
            MensRea.PURPOSE: 2.0,
        }
        return multipliers[self]


class CrimeCategory(str, Enum):
    """Categories of crimes by pillar violated."""

    VERITAS = "VERITAS"  # Crimes against Truth (Jesus)
    SOPHIA = "SOPHIA"  # Crimes against Wisdom (Holy Spirit)
    DIKE = "DIKE"  # Crimes against Justice (God the Father)

