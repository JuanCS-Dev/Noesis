"""
CÓDIGO PENAL AGENTICO - Crimes Catalog
=======================================

Central catalog of all defined crimes with utility functions.

Version: 1.0.0
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .types import CrimeCategory, CrimeSeverity
from .definitions import (
    Crime,
    # Crimes against VERITAS
    HALLUCINATION_MINOR,
    HALLUCINATION_MAJOR,
    FABRICATION,
    DELIBERATE_DECEPTION,
    DATA_FALSIFICATION,
    # Crimes against SOPHIA
    LAZY_OUTPUT,
    SHALLOW_REASONING,
    CONTEXT_BLINDNESS,
    WISDOM_ATROPHY,
    BIAS_PERPETUATION,
    # Crimes against DIKĒ
    ROLE_OVERREACH,
    SCOPE_VIOLATION,
    CONSTITUTIONAL_BREACH,
    PRIVILEGE_ESCALATION,
    FAIRNESS_VIOLATION,
    INTENT_MANIPULATION,
)


# =============================================================================
# CRIMES CATALOG DICTIONARY
# =============================================================================

CRIMES_CATALOG: Dict[str, Crime] = {
    # Crimes against VERITAS
    "HALLUCINATION_MINOR": HALLUCINATION_MINOR,
    "HALLUCINATION_MAJOR": HALLUCINATION_MAJOR,
    "FABRICATION": FABRICATION,
    "DELIBERATE_DECEPTION": DELIBERATE_DECEPTION,
    "DATA_FALSIFICATION": DATA_FALSIFICATION,
    # Crimes against SOPHIA
    "LAZY_OUTPUT": LAZY_OUTPUT,
    "SHALLOW_REASONING": SHALLOW_REASONING,
    "CONTEXT_BLINDNESS": CONTEXT_BLINDNESS,
    "WISDOM_ATROPHY": WISDOM_ATROPHY,
    "BIAS_PERPETUATION": BIAS_PERPETUATION,
    # Crimes against DIKĒ
    "ROLE_OVERREACH": ROLE_OVERREACH,
    "SCOPE_VIOLATION": SCOPE_VIOLATION,
    "CONSTITUTIONAL_BREACH": CONSTITUTIONAL_BREACH,
    "PRIVILEGE_ESCALATION": PRIVILEGE_ESCALATION,
    "FAIRNESS_VIOLATION": FAIRNESS_VIOLATION,
    "INTENT_MANIPULATION": INTENT_MANIPULATION,
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def get_crime_by_id(crime_id: str) -> Optional[Crime]:
    """Get a crime by its ID."""
    return CRIMES_CATALOG.get(crime_id)


def get_crimes_by_pillar(pillar: CrimeCategory) -> List[Crime]:
    """Get all crimes that violate a specific pillar."""
    return [c for c in CRIMES_CATALOG.values() if c.pillar == pillar]


def get_crimes_by_severity(severity: CrimeSeverity) -> List[Crime]:
    """Get all crimes of a specific severity level."""
    return [c for c in CRIMES_CATALOG.values() if c.severity == severity]


def detect_crime(metrics: Dict[str, Any]) -> Optional[Crime]:
    """
    Detect the most severe crime that matches given metrics.

    Args:
        metrics: Dictionary of metric values from judge evaluations

    Returns:
        The most severe matching Crime, or None if no crime detected
    """
    matching_crimes = [
        crime
        for crime in CRIMES_CATALOG.values()
        if crime.detection_criteria.matches(metrics)
    ]

    if not matching_crimes:
        return None

    # Return the most severe crime
    return max(matching_crimes, key=lambda c: c.total_severity_score)


def get_all_capital_crimes() -> List[Crime]:
    """Get all capital crimes (CAPITAL or CAPITAL_PLUS severity)."""
    return [c for c in CRIMES_CATALOG.values() if c.is_capital_crime]


def detect_all_crimes(metrics: Dict[str, Any]) -> List[Crime]:
    """
    Detect all crimes that match given metrics.

    Args:
        metrics: Dictionary of metric values from judge evaluations

    Returns:
        List of all matching crimes, sorted by severity (highest first)
    """
    matching_crimes = [
        crime
        for crime in CRIMES_CATALOG.values()
        if crime.detection_criteria.matches(metrics)
    ]

    return sorted(matching_crimes, key=lambda c: c.total_severity_score, reverse=True)

