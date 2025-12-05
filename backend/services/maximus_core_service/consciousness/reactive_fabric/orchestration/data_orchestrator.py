"""Data Orchestrator - ESGT Trigger Generation from metrics and events."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from consciousness.esgt.coordinator import SalienceScore
from consciousness.reactive_fabric.collectors.event_collector import (
    ConsciousnessEvent,
    EventCollector,
    EventSeverity,
)
from consciousness.reactive_fabric.collectors.metrics_collector import (
    MetricsCollector,
    SystemMetrics,
)
from consciousness.reactive_fabric.orchestration.data_orchestrator_models import (
    OrchestrationDecision,
)

logger = logging.getLogger(__name__)


class DataOrchestrator:
    """Orchestrates metrics and events to generate ESGT triggers."""

    def __init__(
        self,
        consciousness_system: Any,
        collection_interval_ms: float = 100.0,
        salience_threshold: float = 0.65,
        event_buffer_size: int = 1000,
        decision_history_size: int = 100,
    ) -> None:
        """Initialize data orchestrator."""
        self.system = consciousness_system
        self.collection_interval_ms = collection_interval_ms
        self.salience_threshold = salience_threshold

        self.metrics_collector = MetricsCollector(consciousness_system)
        self.event_collector = EventCollector(consciousness_system, max_events=event_buffer_size)

        self._running = False
        self._orchestration_task: Optional[asyncio.Task] = None

        self.total_collections = 0
        self.total_triggers_generated = 0
        self.total_triggers_executed = 0

        self.decision_history: List[OrchestrationDecision] = []
        self.MAX_HISTORY = decision_history_size

        logger.info(
            f"DataOrchestrator initialized: interval={collection_interval_ms}ms, "
            f"threshold={salience_threshold}"
        )

    async def start(self) -> None:
        """Start orchestrator background loop."""
        if self._running:
            logger.warning("Orchestrator already running")
            return

        self._running = True
        self._orchestration_task = asyncio.create_task(self._orchestration_loop())
        logger.info("🎼 DataOrchestrator started - reactive fabric active")

    async def stop(self) -> None:
        """Stop orchestrator background loop."""
        if not self._running:
            return

        self._running = False

        if self._orchestration_task:
            self._orchestration_task.cancel()
            try:
                await self._orchestration_task
            except asyncio.CancelledError:
                # Task cancelled
                return

        logger.info("DataOrchestrator stopped")

    async def _orchestration_loop(self) -> None:
        """Main orchestration loop - runs continuously."""
        logger.info("Orchestration loop started")

        while self._running:
            try:
                await self._collect_and_orchestrate()
                await asyncio.sleep(self.collection_interval_ms / 1000.0)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in orchestration loop: {e}")
                await asyncio.sleep(1.0)

        logger.info("Orchestration loop stopped")

    async def _collect_and_orchestrate(self) -> None:
        """Collect data and generate ESGT triggers if needed."""
        self.total_collections += 1

        try:
            metrics = await self.metrics_collector.collect()
            events = await self.event_collector.collect_events()
            decision = await self._analyze_and_decide(metrics, events)

            self.decision_history.append(decision)
            if len(self.decision_history) > self.MAX_HISTORY:
                self.decision_history.pop(0)

            if decision.should_trigger_esgt:
                await self._execute_esgt_trigger(decision)

        except Exception as e:
            logger.error(f"Error in collect_and_orchestrate: {e}")

    async def _analyze_and_decide(
        self, metrics: SystemMetrics, events: List[ConsciousnessEvent]
    ) -> OrchestrationDecision:
        """Analyze metrics and events to decide if ESGT should be triggered."""
        now = time.time()

        novelty = self._calculate_novelty(metrics, events)
        relevance = self._calculate_relevance(metrics, events)
        urgency = self._calculate_urgency(metrics, events)

        salience = SalienceScore(
            novelty=novelty, relevance=relevance, urgency=urgency, confidence=0.9
        )

        total_salience = salience.compute_total()
        should_trigger = total_salience >= self.salience_threshold

        triggering_events = [
            e for e in events if e.novelty >= 0.7 or e.relevance >= 0.8 or e.urgency >= 0.8
        ]

        reason = self._generate_decision_reason(
            should_trigger, salience, metrics, triggering_events
        )
        confidence = self._calculate_confidence(metrics, events, salience)

        decision = OrchestrationDecision(
            should_trigger_esgt=should_trigger,
            salience=salience,
            reason=reason,
            triggering_events=triggering_events,
            metrics_snapshot=metrics,
            timestamp=now,
            confidence=confidence,
        )

        if should_trigger:
            logger.info(
                f"🎯 Orchestrator decision: TRIGGER ESGT "
                f"(salience={total_salience:.2f}, novelty={novelty:.2f}, "
                f"relevance={relevance:.2f}, urgency={urgency:.2f})"
            )
        else:
            logger.debug(
                f"Orchestrator decision: No trigger "
                f"(salience={total_salience:.2f} < threshold={self.salience_threshold})"
            )

        return decision

    def _calculate_novelty(self, metrics: SystemMetrics, events: List[ConsciousnessEvent]) -> float:
        """Calculate novelty component of salience (0-1)."""
        novelty = 0.5

        if events:
            event_novelties = []
            for event in events:
                weight = 1.0
                if event.severity == EventSeverity.CRITICAL:
                    weight = 1.5
                elif event.severity == EventSeverity.HIGH:
                    weight = 1.2
                event_novelties.append(event.novelty * weight)

            novelty = sum(event_novelties) / len(event_novelties)

        if metrics.esgt_frequency_hz < 1.0:
            novelty += 0.1

        if metrics.arousal_level < 0.2 or metrics.arousal_level > 0.9:
            novelty += 0.2

        return min(1.0, novelty)

    def _calculate_relevance(
        self, metrics: SystemMetrics, events: List[ConsciousnessEvent]
    ) -> float:
        """Calculate relevance component of salience (0-1)."""
        relevance = 0.5

        if events:
            relevances = [e.relevance for e in events]
            relevance = sum(relevances) / len(relevances)

        if metrics.health_score < 0.7:
            relevance += 0.2

        if metrics.pfc_signals_processed > 0:
            relevance += 0.1

        if metrics.safety_violations > 0:
            relevance = min(1.0, relevance + 0.3)

        return min(1.0, relevance)

    def _calculate_urgency(self, metrics: SystemMetrics, events: List[ConsciousnessEvent]) -> float:
        """Calculate urgency component of salience (0-1)."""
        urgency = 0.3

        if events:
            urgency = max(e.urgency for e in events)

        if metrics.safety_violations > 0:
            urgency = max(urgency, 0.9)

        if metrics.kill_switch_active:
            urgency = 1.0

        if metrics.arousal_level < 0.2 or metrics.arousal_level > 0.9:
            urgency = max(urgency, 0.6)

        return min(1.0, urgency)

    def _generate_decision_reason(
        self,
        should_trigger: bool,
        salience: SalienceScore,
        metrics: SystemMetrics,
        triggering_events: List[ConsciousnessEvent],
    ) -> str:
        """Generate human-readable reason for decision."""
        if not should_trigger:
            return f"Salience below threshold ({salience.compute_total():.2f} < {self.salience_threshold})"

        reasons = []

        if triggering_events:
            event_types = set(e.event_type.value for e in triggering_events)
            reasons.append(
                f"{len(triggering_events)} high-salience events ({', '.join(event_types)})"
            )

        if metrics.safety_violations > 0:
            reasons.append(f"{metrics.safety_violations} safety violations")

        if metrics.health_score < 0.7:
            reasons.append(f"low system health ({metrics.health_score:.2f})")

        if metrics.pfc_signals_processed > 0:
            reasons.append("PFC social cognition active")

        if not reasons:
            reasons.append("high computed salience")

        return "ESGT trigger: " + ", ".join(reasons)

    def _calculate_confidence(
        self,
        metrics: SystemMetrics,
        events: List[ConsciousnessEvent],
        salience: SalienceScore,
    ) -> float:
        """Calculate confidence in orchestration decision (0-1)."""
        confidence = 1.0

        if metrics.errors:
            confidence -= 0.1 * len(metrics.errors)

        if metrics.health_score < 0.5:
            confidence -= 0.2

        salience_components = [salience.novelty, salience.relevance, salience.urgency]
        variance = max(salience_components) - min(salience_components)
        if variance > 0.5:
            confidence -= 0.1

        return max(0.0, min(1.0, confidence))

    async def _execute_esgt_trigger(self, decision: OrchestrationDecision) -> None:
        """Execute ESGT trigger based on orchestration decision."""
        self.total_triggers_generated += 1

        try:
            content = {
                "type": "orchestrated_trigger",
                "reason": decision.reason,
                "triggering_events": [
                    {
                        "event_id": e.event_id,
                        "type": e.event_type.value,
                        "severity": e.severity.value,
                        "source": e.source,
                    }
                    for e in decision.triggering_events
                ],
                "metrics": {
                    "health_score": decision.metrics_snapshot.health_score,
                    "arousal": decision.metrics_snapshot.arousal_level,
                    "esgt_success_rate": decision.metrics_snapshot.esgt_success_rate,
                },
                "confidence": decision.confidence,
            }

            event = await self.system.esgt_coordinator.initiate_esgt(
                salience=decision.salience,
                content=content,
                content_source="DataOrchestrator",
            )

            if event.success:
                self.total_triggers_executed += 1
                logger.info(
                    f"✅ ESGT trigger executed successfully: "
                    f"event_id={event.event_id}, coherence={event.achieved_coherence:.2f}"
                )
            else:
                logger.warning(f"⚠️  ESGT trigger failed: {event.failure_reason}")

            for e in decision.triggering_events:
                self.event_collector.mark_processed(e.event_id)
                e.esgt_triggered = True

        except Exception as e:
            logger.error(f"Error executing ESGT trigger: {e}")

    def get_orchestration_stats(self) -> Dict[str, Any]:
        """Get orchestration statistics."""
        metrics_stats = self.metrics_collector.get_collection_stats()
        event_stats = self.event_collector.get_collection_stats()

        return {
            "total_collections": self.total_collections,
            "total_triggers_generated": self.total_triggers_generated,
            "total_triggers_executed": self.total_triggers_executed,
            "trigger_execution_rate": (
                self.total_triggers_executed / max(1, self.total_triggers_generated)
            ),
            "decision_history_size": len(self.decision_history),
            "metrics_collector": metrics_stats,
            "event_collector": event_stats,
            "collection_interval_ms": self.collection_interval_ms,
            "salience_threshold": self.salience_threshold,
        }

    def get_recent_decisions(self, limit: int = 10) -> List[OrchestrationDecision]:
        """Get recent orchestration decisions (newest first)."""
        recent = self.decision_history[-limit:]
        return sorted(recent, key=lambda d: d.timestamp, reverse=True)

    def __repr__(self) -> str:
        return (
            f"DataOrchestrator(running={self._running}, "
            f"collections={self.total_collections}, "
            f"triggers={self.total_triggers_executed}/{self.total_triggers_generated})"
        )
