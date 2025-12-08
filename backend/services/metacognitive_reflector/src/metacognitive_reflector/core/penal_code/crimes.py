"""
CÓDIGO PENAL AGENTICO - Crime Definitions (Re-exports)
=======================================================

This module re-exports all crime-related types and definitions.
Implementation split for CODE_CONSTITUTION compliance (<500 lines).

Version: 1.0.0
"""

# Re-export types
from .types import CrimeSeverity, MensRea, CrimeCategory

# Re-export detection criteria
from .detection import DetectionCriteria

# Re-export crime dataclass and definitions
from .definitions import (
    Crime,
    HALLUCINATION_MINOR,
    HALLUCINATION_MAJOR,
    FABRICATION,
    DELIBERATE_DECEPTION,
    DATA_FALSIFICATION,
    LAZY_OUTPUT,
    SHALLOW_REASONING,
    CONTEXT_BLINDNESS,
    WISDOM_ATROPHY,
    BIAS_PERPETUATION,
    ROLE_OVERREACH,
    SCOPE_VIOLATION,
    CONSTITUTIONAL_BREACH,
    PRIVILEGE_ESCALATION,
    FAIRNESS_VIOLATION,
    INTENT_MANIPULATION,
)

# Re-export catalog and utilities
from .catalog import (
    CRIMES_CATALOG,
    get_crime_by_id,
    get_crimes_by_pillar,
    get_crimes_by_severity,
    detect_crime,
    get_all_capital_crimes,
    detect_all_crimes,
)

__all__ = [
    # Types
    "CrimeSeverity",
    "MensRea",
    "CrimeCategory",
    "DetectionCriteria",
    "Crime",
    # Crimes - VERITAS
    "HALLUCINATION_MINOR",
    "HALLUCINATION_MAJOR",
    "FABRICATION",
    "DELIBERATE_DECEPTION",
    "DATA_FALSIFICATION",
    # Crimes - SOPHIA
    "LAZY_OUTPUT",
    "SHALLOW_REASONING",
    "CONTEXT_BLINDNESS",
    "WISDOM_ATROPHY",
    "BIAS_PERPETUATION",
    # Crimes - DIKĒ
    "ROLE_OVERREACH",
    "SCOPE_VIOLATION",
    "CONSTITUTIONAL_BREACH",
    "PRIVILEGE_ESCALATION",
    "FAIRNESS_VIOLATION",
    "INTENT_MANIPULATION",
    # Catalog
    "CRIMES_CATALOG",
    # Utilities
    "get_crime_by_id",
    "get_crimes_by_pillar",
    "get_crimes_by_severity",
    "detect_crime",
    "get_all_capital_crimes",
    "detect_all_crimes",
]
