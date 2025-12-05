"""
ESGT Enumerations
=================

Enumerations for ESGT (Evento de Sincronização Global Transitória) protocol.

This module defines the phase states and salience classification levels
used throughout the ESGT ignition protocol.
"""

from __future__ import annotations

from enum import Enum


class ESGTPhase(Enum):
    """Phases of ESGT ignition protocol."""

    IDLE = "idle"
    PREPARE = "prepare"
    SYNCHRONIZE = "synchronize"
    BROADCAST = "broadcast"
    SUSTAIN = "sustain"
    DISSOLVE = "dissolve"
    COMPLETE = "complete"
    FAILED = "failed"


class SalienceLevel(Enum):
    """Classification of information salience."""

    MINIMAL = "minimal"  # <0.25 - background noise
    LOW = "low"  # 0.25-0.50 - peripheral awareness
    MEDIUM = "medium"  # 0.50-0.75 - candidate for consciousness
    HIGH = "high"  # 0.75-0.85 - likely conscious
    CRITICAL = "critical"  # >0.85 - definitely conscious
