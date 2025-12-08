"""
CÓDIGO PENAL AGENTICO - Sentencing (Re-exports)
================================================

This module re-exports all sentencing-related types and classes.
Implementation split for CODE_CONSTITUTION compliance (<500 lines).

Version: 1.0.0
"""

# Re-export sentence types
from .sentence_types import SentenceType

# Re-export factors
from .factors import AggravatingFactor, MitigatingFactor

# Re-export sentence model
from .sentence import CriminalHistoryRecord, Sentence

# Re-export engine
from .engine import SentencingEngine

# Backward compatibility alias
CriminalHistory = CriminalHistoryRecord

__all__ = [
    # Sentence types
    "SentenceType",
    # Factors
    "AggravatingFactor",
    "MitigatingFactor",
    # Sentence model
    "CriminalHistoryRecord",
    "CriminalHistory",  # Backward compatibility
    "Sentence",
    # Engine
    "SentencingEngine",
]
