"""SalienceSPM - Salience Detection for ESGT Trigger Control."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from typing import Any

import numpy as np

from consciousness.esgt.coordinator import SalienceScore
from consciousness.esgt.spm.base import SpecializedProcessingModule, SPMOutput, SPMType
from consciousness.esgt.spm.salience_detector_models import (
    SalienceDetectorConfig,
    SalienceEvent,
    SalienceMode,
    SalienceThresholds,  # Re-export for backward compatibility
)

__all__ = [
    "SalienceSPM",
    "SalienceDetectorConfig",
    "SalienceEvent",
    "SalienceMode",
    "SalienceThresholds",
]


class SalienceSPM(SpecializedProcessingModule):
    """Salience detection SPM - the attention controller of consciousness."""

    def __init__(
        self,
        spm_id: str,
        config: SalienceDetectorConfig | None = None,
    ) -> None:
        """Initialize SalienceSPM."""
        super().__init__(spm_id, SPMType.METACOGNITIVE)

        self.config = config or SalienceDetectorConfig()

        total_weight = (
            self.config.novelty_weight + self.config.relevance_weight + self.config.urgency_weight
        )
        if not (0.99 < total_weight < 1.01):
            raise ValueError(f"Salience weights must sum to 1.0, got {total_weight}")

        self._running: bool = False
        self._monitoring_task: asyncio.Task | None = None

        self._metric_history: dict[str, list[float]] = {}
        self._baseline_values: dict[str, float] = {}
        self._urgency_sources: dict[str, tuple[float, float]] = {}

        self._high_salience_events: list[SalienceEvent] = []
        self._high_salience_callbacks: list[Callable[[SalienceEvent], None]] = []

        self.total_evaluations: int = 0
        self.high_salience_count: int = 0

    async def start(self) -> None:
        """Start salience monitoring."""
        if self._running:
            return

        self._running = True

        if self.config.mode == SalienceMode.ACTIVE:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())

    async def stop(self) -> None:
        """Stop salience monitoring."""
        self._running = False

        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                # Task cancelled
                return

        self._monitoring_task = None

    async def _monitoring_loop(self) -> None:
        """Active monitoring loop - decays urgency and checks timeout conditions."""
        interval_s = self.config.update_interval_ms / 1000.0

        while self._running:
            try:
                self._decay_urgencies()
                await asyncio.sleep(interval_s)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.info("[SalienceSPM %s] Monitoring error: {e}", self.spm_id)
                await asyncio.sleep(interval_s)

    def evaluate_event(
        self,
        source: str,
        content: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> SalienceScore:
        """Evaluate salience of an event."""
        self.total_evaluations += 1

        novelty = self._compute_novelty(source, content)
        relevance = self._compute_relevance(content, context)
        urgency = self._get_current_urgency(source)

        delta_weight = 1.0 - (
            self.config.novelty_weight + self.config.relevance_weight + self.config.urgency_weight
        )

        salience = SalienceScore(
            novelty=novelty,
            relevance=relevance,
            urgency=urgency,
            alpha=self.config.novelty_weight,
            beta=self.config.relevance_weight,
            gamma=self.config.urgency_weight,
            delta=max(0.0, delta_weight),
        )

        total_salience = salience.compute_total()

        if total_salience >= self.config.thresholds.high_threshold:
            self._handle_high_salience(source, content, salience)

        return salience

    def _compute_novelty(self, source: str, content: dict[str, Any]) -> float:
        """Compute novelty via change detection."""
        value = self._extract_tracking_value(content)

        if value is None:
            return 0.55

        if source not in self._metric_history:
            self._metric_history[source] = []

        self._metric_history[source].append(value)

        window = self.config.novelty_baseline_window
        if len(self._metric_history[source]) > window:
            self._metric_history[source].pop(0)

        history = self._metric_history[source]
        if len(history) < 3:
            return 0.55

        baseline = float(np.mean(history[:-1]))
        self._baseline_values[source] = baseline

        if baseline == 0:
            deviation = 1.0 if value > 0 else 0.0
        else:
            deviation = abs(value - baseline) / max(abs(baseline), 1.0)

        novelty = min(1.0, deviation / self.config.novelty_change_threshold)

        return novelty

    def _extract_tracking_value(self, content: dict[str, Any]) -> float | None:
        """Extract a numeric value to track for novelty detection."""
        for key in ["value", "metric", "score", "level", "magnitude"]:
            if key in content:
                val = content[key]
                if isinstance(val, (int, float)):
                    return float(val)

        for val in content.values():
            if isinstance(val, (int, float)):
                return float(val)

        return None

    def _compute_relevance(
        self,
        content: dict[str, Any],
        context: dict[str, Any] | None,
    ) -> float:
        """Compute relevance to current goals/context."""
        relevance_scores = []

        if "relevance" in content:
            relevance_scores.append(float(content["relevance"]))

        if "priority" in content:
            priority = content["priority"]
            priority_map = {"low": 0.3, "medium": 0.5, "high": 0.7, "critical": 0.95}
            if isinstance(priority, str) and priority.lower() in priority_map:
                relevance_scores.append(priority_map[priority.lower()])

        if context and "goal_id" in content and "active_goals" in context:
            active_goals = context["active_goals"]
            if content["goal_id"] in active_goals:
                relevance_scores.append(0.8)

        if context and "need" in content and "current_needs" in context:
            need = content["need"]
            current_needs = context["current_needs"]
            if need in current_needs:
                relevance_scores.append(min(1.0, current_needs[need] * 1.2))

        return max(relevance_scores) if relevance_scores else self.config.default_relevance

    def _get_current_urgency(self, source: str) -> float:
        """Get current urgency level (with decay)."""
        if source not in self._urgency_sources:
            return 0.0

        urgency, timestamp = self._urgency_sources[source]
        elapsed = time.time() - timestamp
        decayed = urgency * np.exp(-self.config.urgency_decay_rate * elapsed)
        self._urgency_sources[source] = (decayed, time.time())

        return float(max(0.0, decayed))

    def set_urgency(self, source: str, urgency: float) -> None:
        """Explicitly set urgency for a source."""
        urgency = max(0.0, min(1.0, urgency))
        self._urgency_sources[source] = (urgency, time.time())

    def boost_urgency_on_error(self, source: str) -> None:
        """Boost urgency when errors detected."""
        current = self._get_current_urgency(source)
        boosted = min(1.0, current + self.config.urgency_boost_on_error)
        self.set_urgency(source, boosted)

    def _decay_urgencies(self) -> None:
        """Decay all urgency sources."""
        for source in list(self._urgency_sources.keys()):
            self._get_current_urgency(source)

            if self._urgency_sources[source][0] < 0.01:
                del self._urgency_sources[source]

    def _handle_high_salience(
        self,
        source: str,
        content: dict[str, Any],
        salience: SalienceScore,
    ) -> None:
        """Handle high-salience detection."""
        self.high_salience_count += 1

        event = SalienceEvent(
            timestamp=time.time(),
            salience=salience,
            source=source,
            content=content,
            threshold_exceeded=self.config.thresholds.high_threshold,
        )

        self._high_salience_events.append(event)
        if len(self._high_salience_events) > self.config.max_history_size:
            self._high_salience_events.pop(0)

        for callback in self._high_salience_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.info("[SalienceSPM %s] Callback error: {e}", self.spm_id)

    async def process(self) -> SPMOutput | None:
        """Process and generate output (required by base class)."""
        return None

    def compute_salience(self, data: dict[str, Any]) -> SalienceScore:
        """Compute salience for given data (required by base class)."""
        return self.evaluate_event(source="compute_salience", content=data, context=None)

    def register_high_salience_callback(self, callback: Callable[[SalienceEvent], None]) -> None:
        """Register callback for high-salience events."""
        if callback not in self._high_salience_callbacks:
            self._high_salience_callbacks.append(callback)

    def get_recent_high_salience_events(self, count: int = 10) -> list[SalienceEvent]:
        """Get recent high-salience events."""
        return self._high_salience_events[-count:]

    def get_salience_rate(self) -> float:
        """Get percentage of evaluations that were high-salience."""
        if self.total_evaluations == 0:
            return 0.0
        return self.high_salience_count / self.total_evaluations

    def get_metrics(self) -> dict[str, Any]:
        """Get detector performance metrics."""
        return {
            "spm_id": self.spm_id,
            "running": self._running,
            "total_evaluations": self.total_evaluations,
            "high_salience_count": self.high_salience_count,
            "salience_rate": self.get_salience_rate(),
            "tracked_sources": len(self._metric_history),
            "active_urgencies": len(self._urgency_sources),
        }

    def __repr__(self) -> str:
        return (
            f"SalienceSPM(id={self.spm_id}, evals={self.total_evaluations}, "
            f"high_salience={self.high_salience_count}, rate={self.get_salience_rate():.1%})"
        )
