"""Data Orchestrator Models - Data structures for orchestration decisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from consciousness.reactive_fabric.collectors.event_collector import ConsciousnessEvent
    from consciousness.reactive_fabric.collectors.metrics_collector import SystemMetrics
    from consciousness.esgt.coordinator import SalienceScore


@dataclass
class OrchestrationDecision:
    """Decision made by orchestrator for ESGT triggering."""

    should_trigger_esgt: bool
    salience: SalienceScore
    reason: str
    triggering_events: List[ConsciousnessEvent]
    metrics_snapshot: SystemMetrics
    timestamp: float
    confidence: float  # 0-1
