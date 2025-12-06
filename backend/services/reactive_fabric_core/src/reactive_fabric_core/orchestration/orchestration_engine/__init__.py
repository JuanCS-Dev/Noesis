"""
Orchestration Engine Package.

Event correlation and threat analysis for Reactive Fabric.
"""

from __future__ import annotations

from .correlator import EventCorrelator
from .engine import OrchestrationEngine
from .models import (
    CorrelationRule,
    EventCorrelationWindow,
    OrchestrationConfig,
    OrchestrationEvent,
    ThreatCategory,
    ThreatScore,
)
from .pattern_detector import PatternDetector
from .threat_scorer import ThreatScorer

__all__ = [
    "CorrelationRule",
    "EventCorrelationWindow",
    "EventCorrelator",
    "OrchestrationConfig",
    "OrchestrationEngine",
    "OrchestrationEvent",
    "PatternDetector",
    "ThreatCategory",
    "ThreatScore",
    "ThreatScorer",
]
