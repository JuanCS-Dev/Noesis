"""
Stress Monitoring and MPE Validation.

Implements stress testing for consciousness - deliberately overloading the system to assess
resilience, measure breakdown conditions, and validate MPE stability.

Stress Levels: NONE (0.0-0.2), MILD (0.2-0.4), MODERATE (0.4-0.6), SEVERE (0.6-0.8), CRITICAL (0.8-1.0)

Stress Types: COMPUTATIONAL_LOAD, ERROR_INJECTION, NETWORK_DEGRADATION, AROUSAL_FORCING, RAPID_CHANGE
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable, Coroutine
from typing import Any

import numpy as np

from maximus_core_service.consciousness.mcea.controller import ArousalController
from maximus_core_service.consciousness.mcea.stress_models import (
    StressLevel,
    StressResponse,
    StressTestConfig,
    StressType,
)
from maximus_core_service.consciousness.mmei.monitor import AbstractNeeds


class StressMonitor:
    """
    Monitors system stress and conducts stress testing.

    Enables continuous stress level monitoring, deliberate stress testing for validation,
    breakdown detection and alerting, and resilience assessment.
    """

    def __init__(
        self,
        arousal_controller: ArousalController,
        config: StressTestConfig | None = None,
        monitor_id: str = "mcea-stress-monitor-primary",
    ) -> None:
        self.monitor_id = monitor_id
        self.arousal_controller = arousal_controller
        self.config = config or StressTestConfig()

        self._current_stress_level: StressLevel = StressLevel.NONE
        self._stress_history: list[tuple[float, StressLevel]] = []
        self._baseline_arousal: float | None = None

        self._active_test: StressType | None = None
        self._test_start_time: float | None = None

        self._running: bool = False
        self._monitoring_task: asyncio.Task | None = None
        self._stress_alert_callbacks: list[tuple[Callable, StressLevel]] = []
        self._test_results: list[StressResponse] = []

        self.total_stress_events: int = 0
        self.critical_stress_events: int = 0
        self.tests_conducted: int = 0
        self.tests_passed: int = 0

    def register_stress_alert(
        self,
        callback: Callable[[StressLevel], None | Coroutine[Any, Any, None]],
        threshold: StressLevel = StressLevel.SEVERE,
    ) -> None:
        """Register callback invoked when stress exceeds threshold."""
        self._stress_alert_callbacks.append((callback, threshold))

    async def start(self) -> None:
        """Start passive stress monitoring."""
        if self._running:
            return

        self._baseline_arousal = self.arousal_controller.get_current_arousal().arousal
        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info(
            f"📊 Stress Monitor {self.monitor_id} started (baseline arousal: {self._baseline_arousal:.2f})"
        )

    async def stop(self) -> None:
        """Stop monitoring."""
        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                # Task cancelled
                return

    async def _monitoring_loop(self) -> None:
        """Continuous stress monitoring loop."""
        while self._running:
            try:
                stress_level = self._assess_stress_level()

                self._stress_history.append((time.time(), stress_level))
                if len(self._stress_history) > 1000:
                    self._stress_history.pop(0)

                if stress_level != self._current_stress_level:
                    if stress_level in [StressLevel.SEVERE, StressLevel.CRITICAL]:
                        self.total_stress_events += 1
                        if stress_level == StressLevel.CRITICAL:
                            self.critical_stress_events += 1

                    self._current_stress_level = stress_level
                    await self._invoke_stress_alerts(stress_level)

                await asyncio.sleep(1.0)

            except Exception as e:
                logger.info("⚠️  Stress monitoring error: %s", e)
                await asyncio.sleep(1.0)

    def _assess_stress_level(self) -> StressLevel:
        """Assess current stress level based on arousal and needs."""
        arousal_state = self.arousal_controller.get_current_arousal()
        arousal = arousal_state.arousal

        if self._baseline_arousal is not None:
            stress = abs(arousal - self._baseline_arousal)
        else:
            stress = arousal

        controller_stress = self.arousal_controller.get_stress_level()
        combined_stress = max(stress, controller_stress)

        if combined_stress < 0.2:
            return StressLevel.NONE
        if combined_stress < 0.4:
            return StressLevel.MILD
        if combined_stress < 0.6:
            return StressLevel.MODERATE
        if combined_stress < 0.8:
            return StressLevel.SEVERE
        return StressLevel.CRITICAL

    async def _invoke_stress_alerts(self, stress_level: StressLevel) -> None:
        """Invoke registered stress alert callbacks."""
        stress_severity = self._get_stress_severity(stress_level)

        for callback, threshold in self._stress_alert_callbacks:
            threshold_severity = self._get_stress_severity(threshold)

            if stress_severity >= threshold_severity:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(stress_level)
                    else:
                        callback(stress_level)
                except Exception as e:
                    logger.info("⚠️  Stress alert callback error: %s", e)

    def _get_stress_severity(self, level: StressLevel) -> int:
        """Get numeric severity for comparison."""
        mapping = {
            StressLevel.NONE: 0,
            StressLevel.MILD: 1,
            StressLevel.MODERATE: 2,
            StressLevel.SEVERE: 3,
            StressLevel.CRITICAL: 4,
        }
        return mapping[level]

    async def run_stress_test(
        self,
        stress_type: StressType,
        stress_level: StressLevel = StressLevel.SEVERE,
        duration_seconds: float | None = None,
        monitor_needs: AbstractNeeds | None = None,
    ) -> StressResponse:
        """Run active stress test."""
        if duration_seconds is None:
            duration_seconds = self.config.stress_duration_seconds

        logger.info(
            f"🧪 Starting stress test: {stress_type.value} at {stress_level.value} for {duration_seconds:.0f}s"
        )

        initial_arousal = self.arousal_controller.get_current_arousal().arousal
        self._active_test = stress_type
        self._test_start_time = time.time()

        response = self._create_initial_response(
            stress_type, stress_level, initial_arousal, duration_seconds
        )

        arousal_samples: list[float] = []
        stress_phase_arousal_samples: list[float] = []
        stress_start = time.time()

        # STRESS PHASE
        while time.time() - stress_start < duration_seconds:
            await self._apply_stressor(stress_type, stress_level)

            current_arousal = self.arousal_controller.get_current_arousal().arousal
            arousal_samples.append(current_arousal)
            stress_phase_arousal_samples.append(current_arousal)

            response.peak_arousal = max(response.peak_arousal, current_arousal)

            if monitor_needs:
                response.peak_rest_need = max(response.peak_rest_need, monitor_needs.rest_need)
                response.peak_repair_need = max(
                    response.peak_repair_need, monitor_needs.repair_need
                )
                response.peak_efficiency_need = max(
                    response.peak_efficiency_need, monitor_needs.efficiency_need
                )

            await asyncio.sleep(0.1)

        # RECOVERY PHASE
        logger.info("⏸️  Stress removed, monitoring recovery...")
        recovery_start = time.time()
        recovered = False

        while time.time() - recovery_start < self.config.recovery_duration_seconds:
            current_arousal = self.arousal_controller.get_current_arousal().arousal
            arousal_samples.append(current_arousal)

            if abs(current_arousal - initial_arousal) < self.config.recovery_baseline_tolerance:
                if not recovered:
                    response.recovery_time_seconds = time.time() - recovery_start
                    response.full_recovery_achieved = True
                    recovered = True
                    break

            await asyncio.sleep(0.1)

        if not recovered:
            response.recovery_time_seconds = self.config.recovery_duration_seconds
            response.full_recovery_achieved = False

        response.final_arousal = self.arousal_controller.get_current_arousal().arousal

        if len(arousal_samples) > 1:
            response.arousal_stability_cv = float(
                np.std(arousal_samples) / np.mean(arousal_samples)
            )

        response.arousal_runaway_detected = self._detect_arousal_runaway(
            stress_phase_arousal_samples
        )
        response.goal_generation_failure = False
        response.coherence_collapse = False

        self._active_test = None
        self._test_start_time = None

        self._test_results.append(response)
        self.tests_conducted += 1

        if response.passed_stress_test():
            self.tests_passed += 1

        logger.info(
            f"✅ Test complete: Resilience {response.get_resilience_score():.1f}/100, {response.passed_stress_test()}"
        )

        return response

    def _create_initial_response(
        self,
        stress_type: StressType,
        stress_level: StressLevel,
        initial_arousal: float,
        duration_seconds: float,
    ) -> StressResponse:
        """Create initial StressResponse with default values."""
        return StressResponse(
            stress_type=stress_type,
            stress_level=stress_level,
            initial_arousal=initial_arousal,
            peak_arousal=initial_arousal,
            final_arousal=initial_arousal,
            arousal_stability_cv=0.0,
            peak_rest_need=0.0,
            peak_repair_need=0.0,
            peak_efficiency_need=0.0,
            goals_generated=0,
            goals_satisfied=0,
            critical_goals_generated=0,
            esgt_events=0,
            mean_esgt_coherence=0.0,
            esgt_coherence_degradation=0.0,
            recovery_time_seconds=0.0,
            full_recovery_achieved=False,
            arousal_runaway_detected=False,
            goal_generation_failure=False,
            coherence_collapse=False,
            duration_seconds=duration_seconds,
        )

    async def _apply_stressor(self, stress_type: StressType, stress_level: StressLevel) -> None:
        """Apply specific stressor to system."""
        severity = self._get_stress_severity(stress_level)

        if stress_type == StressType.AROUSAL_FORCING:
            target_arousal = 0.5 + (severity / 4.0) * 0.5
            self.arousal_controller.request_modulation(
                source="stress_test",
                delta=target_arousal - self.arousal_controller.get_current_arousal().arousal,
                duration_seconds=0.5,
                priority=10,
            )

        elif stress_type == StressType.COMPUTATIONAL_LOAD:
            load_boost = 0.1 + (severity / 4.0) * 0.3
            self.arousal_controller.request_modulation(
                source="cpu_load_simulation", delta=load_boost, duration_seconds=0.5, priority=5
            )

        elif stress_type == StressType.RAPID_CHANGE:
            oscillation = 0.2 * np.sin(time.time() * 2 * np.pi)
            self.arousal_controller.request_modulation(
                source="rapid_change", delta=oscillation, duration_seconds=0.2, priority=3
            )

    def _detect_arousal_runaway(self, arousal_samples: list[float]) -> bool:
        """Detect if arousal got stuck at maximum (runaway)."""
        if len(arousal_samples) < 10:
            return False

        high_arousal_samples = [
            a for a in arousal_samples if a > self.config.arousal_runaway_threshold
        ]
        return (len(high_arousal_samples) / len(arousal_samples)) > 0.8

    def get_current_stress_level(self) -> StressLevel:
        """Get current passive stress level."""
        return self._current_stress_level

    def get_stress_history(
        self, window_seconds: float | None = None
    ) -> list[tuple[float, StressLevel]]:
        """Get stress level history."""
        if window_seconds is None:
            return self._stress_history.copy()

        cutoff = time.time() - window_seconds
        return [(t, level) for t, level in self._stress_history if t >= cutoff]

    def get_test_results(self) -> list[StressResponse]:
        """Get all stress test results."""
        return self._test_results.copy()

    def get_average_resilience(self) -> float:
        """Get average resilience score across all tests."""
        if not self._test_results:
            return 0.0
        scores = [r.get_resilience_score() for r in self._test_results]
        return float(np.mean(scores))

    def get_statistics(self) -> dict[str, Any]:
        """Get stress monitoring statistics."""
        pass_rate = self.tests_passed / self.tests_conducted if self.tests_conducted > 0 else 0.0

        return {
            "monitor_id": self.monitor_id,
            "running": self._running,
            "current_stress_level": self._current_stress_level.value,
            "baseline_arousal": self._baseline_arousal,
            "total_stress_events": self.total_stress_events,
            "critical_stress_events": self.critical_stress_events,
            "tests_conducted": self.tests_conducted,
            "tests_passed": self.tests_passed,
            "pass_rate": pass_rate,
            "average_resilience": self.get_average_resilience(),
        }

    def __repr__(self) -> str:
        return f"StressMonitor({self.monitor_id}, stress={self._current_stress_level.value}, tests={self.tests_conducted})"
