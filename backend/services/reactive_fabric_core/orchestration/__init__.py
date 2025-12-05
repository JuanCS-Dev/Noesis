"""
Orchestration Engine for Reactive Fabric.

Correlates events from multiple collectors and identifies patterns.
Phase 1: PASSIVE orchestration only - no automated responses.
"""

from __future__ import annotations


from .orchestration_engine import (
    CorrelationRule,
    EventCorrelationWindow,
    EventCorrelator,
    OrchestrationConfig,
    OrchestrationEngine,
    OrchestrationEvent,
    PatternDetector,
    ThreatCategory,
    ThreatScore,
    ThreatScorer,
)

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