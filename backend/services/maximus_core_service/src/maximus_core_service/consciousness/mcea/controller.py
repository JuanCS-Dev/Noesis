"""
Arousal Control System - MPE Foundation.

Controls global arousal/excitability that modulates ESGT ignition threshold.
Based on ARAS and neuromodulatory systems (norepinephrine, acetylcholine, etc.)
"""

from __future__ import annotations

import asyncio
import logging
import math
import time
from collections import deque
from collections.abc import Callable, Coroutine

import numpy as np

logger = logging.getLogger(__name__)

from maximus_core_service.consciousness.mmei.monitor import AbstractNeeds

from .models import ArousalConfig, ArousalLevel, ArousalModulation, ArousalState
from .safety import (
    AROUSAL_OSCILLATION_THRESHOLD,
    AROUSAL_OSCILLATION_WINDOW,
    AROUSAL_SATURATION_THRESHOLD_SECONDS,
    MAX_AROUSAL_DELTA_PER_SECOND,
    ArousalBoundEnforcer,
    ArousalRateLimiter,
)


class ArousalController:
    """
    Controls global arousal/excitability state for ESGT ignition modulation.

    Updates arousal based on: internal needs (MMEI), external events,
    temporal dynamics (stress, recovery, circadian), and ESGT history.
    """

    def __init__(
        self,
        config: ArousalConfig | None = None,
        controller_id: str = "mcea-arousal-controller-primary",
    ):
        self.controller_id = controller_id
        self.config = config or ArousalConfig()

        self._current_state: ArousalState = ArousalState(arousal=self.config.baseline_arousal)
        self._target_arousal: float = self.config.baseline_arousal
        self._active_modulations: list[ArousalModulation] = []
        self._accumulated_stress: float = 0.0
        self._refractory_until: float | None = None

        self._running: bool = False
        self._update_task: asyncio.Task | None = None

        self._last_level: ArousalLevel = self._current_state.level
        self._level_transition_time: float = time.time()
        self._arousal_callbacks: list[Callable[[ArousalState], None]] = []

        # Statistics
        self.total_updates: int = 0
        self.total_modulations: int = 0
        self.esgt_refractories_applied: int = 0

        # FASE VII (Safety Hardening)
        self.rate_limiter = ArousalRateLimiter(max_delta_per_second=MAX_AROUSAL_DELTA_PER_SECOND)
        self.arousal_history: deque = deque(maxlen=AROUSAL_OSCILLATION_WINDOW)
        self.arousal_saturation_start: float | None = None
        self.saturation_events: int = 0
        self.oscillation_events: int = 0
        self.invalid_needs_count: int = 0

    def _classify_arousal(self, arousal: float) -> ArousalLevel:
        """Classify arousal value into level."""
        if arousal <= 0.2:
            return ArousalLevel.SLEEP
        elif arousal <= 0.4:
            return ArousalLevel.DROWSY
        elif arousal <= 0.6:
            return ArousalLevel.RELAXED
        elif arousal <= 0.8:
            return ArousalLevel.ALERT
        else:
            return ArousalLevel.HYPERALERT

    def register_arousal_callback(
        self, callback: Callable[[ArousalState], None | Coroutine[Any, Any, None]]
    ) -> None:
        """Register callback invoked on arousal state changes."""
        self._arousal_callbacks.append(callback)

    async def start(self) -> None:
        """Start continuous arousal updates."""
        if self._running:
            return
        self._running = True
        self._update_task = asyncio.create_task(self._update_loop())
        logger.info("🌅 MCEA Arousal Controller %s started (MPE active)", self.controller_id)

    async def stop(self) -> None:
        """Stop controller."""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                # Task cancelled
                return

    async def _update_loop(self) -> None:
        """Continuous arousal update loop."""
        interval = self.config.update_interval_ms / 1000.0
        while self._running:
            try:
                await self._update_arousal(interval)
                self.total_updates += 1
                await asyncio.sleep(interval)
            except Exception as e:
                logger.info("⚠️  Arousal update error: %s", e)
                await asyncio.sleep(interval)

    async def _update_arousal(self, dt: float) -> None:
        """Update arousal state."""
        need_contrib = self._current_state.need_contribution
        external_contrib = self._compute_external_contribution()
        temporal_contrib = self._compute_temporal_contribution(dt)
        circadian_contrib = self._compute_circadian_contribution()

        target = (
            self.config.baseline_arousal
            + need_contrib
            + external_contrib
            + temporal_contrib
            + circadian_contrib
        )

        if self._refractory_until and time.time() < self._refractory_until:
            target -= self.config.esgt_refractory_arousal_drop

        target = np.clip(target, self.config.min_arousal, self.config.max_arousal)
        current = self._current_state.arousal

        if target > current:
            delta = self.config.arousal_increase_rate * dt
            new_arousal = min(current + delta, target)
        else:
            delta = self.config.arousal_decrease_rate * dt
            new_arousal = max(current - delta, target)

        new_arousal = self.rate_limiter.limit(new_arousal, time.time())
        new_arousal = ArousalBoundEnforcer.enforce(new_arousal)

        self.arousal_history.append(new_arousal)
        self._detect_saturation(new_arousal)
        self._detect_oscillation()

        old_level = self._current_state.level
        self._current_state = ArousalState(
            arousal=new_arousal,
            baseline_arousal=self.config.baseline_arousal,
            need_contribution=need_contrib,
            external_contribution=external_contrib,
            temporal_contribution=temporal_contrib,
            circadian_contribution=circadian_contrib,
            esgt_salience_threshold=self._current_state.compute_effective_threshold(),
        )
        self._current_state.esgt_salience_threshold = (
            self._current_state.compute_effective_threshold()
        )

        if self._current_state.level != old_level:
            duration = time.time() - self._level_transition_time
            self._current_state.time_in_current_level_seconds = duration
            self._level_transition_time = time.time()
            self._last_level = self._current_state.level

        await self._invoke_callbacks()

    def _compute_external_contribution(self) -> float:
        """Compute external modulation contribution."""
        expired = [m for m in self._active_modulations if m.is_expired()]
        for m in expired:
            self._active_modulations.remove(m)

        if not self._active_modulations:
            return 0.0

        self._active_modulations.sort(key=lambda m: m.priority, reverse=True)
        total = 0.0
        weights_sum = 0.0
        for m in self._active_modulations[:3]:
            weight = m.priority
            total += m.get_current_delta() * weight
            weights_sum += weight
        return total / weights_sum if weights_sum > 0 else 0.0

    def _compute_temporal_contribution(self, dt: float) -> float:
        """Compute stress/recovery temporal contribution."""
        if self._current_state.arousal > 0.7:
            self._accumulated_stress += self.config.stress_buildup_rate * dt
        elif self._current_state.arousal < 0.5:
            self._accumulated_stress -= self.config.stress_recovery_rate * dt
        self._accumulated_stress = max(0.0, min(0.3, self._accumulated_stress))
        return self._accumulated_stress

    def _compute_circadian_contribution(self) -> float:
        """Compute circadian rhythm contribution (if enabled)."""
        if not self.config.enable_circadian:
            return 0.0
        hour = time.localtime().tm_hour
        phase = (hour - 6) / 24.0 * 2 * math.pi
        return self.config.circadian_amplitude * math.sin(phase)

    async def _invoke_callbacks(self) -> None:
        """Invoke registered callbacks."""
        for callback in self._arousal_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self._current_state)
                else:
                    callback(self._current_state)
            except Exception as e:
                logger.info("⚠️  Callback error: %s", e)

    def get_current_arousal(self) -> ArousalState:
        """Get current arousal state."""
        return self._current_state

    def get_esgt_threshold(self) -> float:
        """Get effective ESGT salience threshold."""
        return self._current_state.esgt_salience_threshold

    def request_modulation(
        self,
        source: str,
        delta: float,
        duration_seconds: float = 0.0,
        priority: int = 1,
    ) -> None:
        """Request arousal modulation from external source."""
        modulation = ArousalModulation(
            source=source,
            delta=delta,
            duration_seconds=duration_seconds,
            priority=priority,
        )
        self._active_modulations.append(modulation)
        self.total_modulations += 1

    def update_from_needs(self, needs: AbstractNeeds) -> None:
        """Update arousal based on MMEI needs."""
        if not self._validate_needs(needs):
            self.invalid_needs_count += 1
            return

        contribution = 0.0
        contribution += needs.repair_need * self.config.repair_need_weight
        contribution += needs.rest_need * self.config.rest_need_weight
        contribution += needs.efficiency_need * self.config.efficiency_need_weight
        contribution += needs.connectivity_need * self.config.connectivity_need_weight
        self._current_state.need_contribution = contribution

    def apply_esgt_refractory(self) -> None:
        """Apply refractory period after ESGT event."""
        self._refractory_until = time.time() + self.config.esgt_refractory_duration_seconds
        self.esgt_refractories_applied += 1

    def get_stress_level(self) -> float:
        """Get current accumulated stress."""
        return self._accumulated_stress

    def reset_stress(self) -> None:
        """Reset accumulated stress."""
        self._accumulated_stress = 0.0

    def get_statistics(self) -> dict[str, any]:
        """Get controller statistics."""
        return {
            "controller_id": self.controller_id,
            "running": self._running,
            "total_updates": self.total_updates,
            "total_modulations": self.total_modulations,
            "esgt_refractories_applied": self.esgt_refractories_applied,
            "active_modulations": len(self._active_modulations),
            "accumulated_stress": self._accumulated_stress,
            "current_arousal": self._current_state.arousal,
            "current_level": self._current_state.level.value,
            "esgt_threshold": self._current_state.esgt_salience_threshold,
        }

    def _validate_needs(self, needs: AbstractNeeds) -> bool:
        """Validate AbstractNeeds input."""
        if needs is None:
            return False
        need_values = [
            needs.rest_need,
            needs.repair_need,
            needs.efficiency_need,
            needs.connectivity_need,
            needs.curiosity_drive,
            needs.learning_drive,
        ]
        for value in need_values:
            if not isinstance(value, (int, float)) or value < 0.0 or value > 1.0:
                return False
        return True

    def _detect_saturation(self, arousal: float) -> None:
        """Detect arousal saturation (stuck at 0.0 or 1.0)."""
        at_boundary = arousal <= 0.01 or arousal >= 0.99
        if at_boundary:
            if self.arousal_saturation_start is None:
                self.arousal_saturation_start = time.time()
            else:
                duration = time.time() - self.arousal_saturation_start
                if duration >= AROUSAL_SATURATION_THRESHOLD_SECONDS:
                    self.saturation_events += 1
                    logger.info("⚠️  MCEA SATURATION: Arousal stuck at %.2f for {duration:.1f}s", arousal)
                    self.arousal_saturation_start = time.time()
        else:
            self.arousal_saturation_start = None

    def _detect_oscillation(self) -> None:
        """Detect arousal oscillation (high variance)."""
        if len(self.arousal_history) < AROUSAL_OSCILLATION_WINDOW:
            return
        stddev = float(np.std(self.arousal_history))
        if stddev > AROUSAL_OSCILLATION_THRESHOLD:
            self.oscillation_events += 1
            logger.info("⚠️  MCEA OSCILLATION: variance=%.3f", stddev)

    def get_health_metrics(self) -> dict[str, any]:
        """Get MCEA health metrics for Safety Core integration."""
        arousal_variance = (
            float(np.std(self.arousal_history)) if len(self.arousal_history) >= 2 else 0.0
        )
        is_saturated = False
        if self.arousal_saturation_start:
            saturation_duration = time.time() - self.arousal_saturation_start
            is_saturated = saturation_duration >= AROUSAL_SATURATION_THRESHOLD_SECONDS

        return {
            "controller_id": self.controller_id,
            "running": self._running,
            "current_arousal": self._current_state.arousal,
            "current_level": self._current_state.level.value,
            "esgt_threshold": self._current_state.esgt_salience_threshold,
            "accumulated_stress": self._accumulated_stress,
            "total_updates": self.total_updates,
            "total_modulations": self.total_modulations,
            "esgt_refractories": self.esgt_refractories_applied,
            "saturation_events": self.saturation_events,
            "oscillation_events": self.oscillation_events,
            "invalid_needs_count": self.invalid_needs_count,
            "is_saturated": is_saturated,
            "arousal_variance": arousal_variance,
            "arousal_history_size": len(self.arousal_history),
        }

    def __repr__(self) -> str:
        return (
            f"ArousalController({self.controller_id}, "
            f"arousal={self._current_state.arousal:.2f}, "
            f"level={self._current_state.level.value})"
        )
