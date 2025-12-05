"""MMEI Internal State Monitor - Computational interoception for AI consciousness."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable, Coroutine
from typing import Any

import numpy as np

from consciousness.mmei.goal_manager import GoalManager
from consciousness.mmei.models import (
    AbstractNeeds,
    Goal,
    GOAL_DEDUP_WINDOW_SECONDS,  # Re-export for backward compatibility
    InteroceptionConfig,
    MAX_ACTIVE_GOALS,  # Re-export for backward compatibility
    MAX_GOALS_PER_MINUTE,  # Re-export for backward compatibility
    NeedUrgency,
    PhysicalMetrics,
)
from consciousness.mmei.needs_computation import NeedsComputation
from consciousness.mmei.rate_limiter import RateLimiter  # Re-export for backward compat

__all__ = [
    "InternalStateMonitor",
    "AbstractNeeds",
    "Goal",
    "InteroceptionConfig",
    "NeedUrgency",
    "PhysicalMetrics",
    "GOAL_DEDUP_WINDOW_SECONDS",
    "MAX_ACTIVE_GOALS",
    "MAX_GOALS_PER_MINUTE",
    "RateLimiter",
]


class InternalStateMonitor:
    """
    Monitors internal physical/computational state and translates to abstract needs.

    This is the core interoception engine - continuously collecting physical
    metrics and computing phenomenal "feelings" (abstract needs).

    Architecture:
    -------------
    Physical Layer:
      ↓ (metrics collection)
    PhysicalMetrics
      ↓ (translation)
    AbstractNeeds
      ↓ (goal generation)
    Autonomous Goals → ESGT → HCL

    The monitor runs continuously in background (~10 Hz), maintaining
    moving averages to prevent oscillation and computing needs based on
    both short-term and long-term trends.

    Integration Points:
    -------------------
    - HCL: Receives goals generated from needs
    - ESGT: Critical needs elevate salience, force ignition
    - Attention: Needs bias attention toward relevant stimuli

    Usage:
    ------
        monitor = InternalStateMonitor(config)

        # Provide metrics collector
        async def collect_metrics() -> PhysicalMetrics:
            return PhysicalMetrics(
                cpu_usage_percent=psutil.cpu_percent(),
                memory_usage_percent=psutil.virtual_memory().percent,
                # ...
            )

        monitor.set_metrics_collector(collect_metrics)
        await monitor.start()

        # Get current needs
        needs = monitor.get_current_needs()
        logger.info("Most urgent: %s", needs.get_most_urgent())

        # Register callback for critical needs
        async def handle_critical(needs: AbstractNeeds):
            logger.info("CRITICAL: %s", needs.get_critical_needs())

        monitor.register_need_callback(handle_critical, threshold=0.80)

    Historical Note:
    ----------------
    First implementation of computational interoception for artificial consciousness.
    Enables embodied cognition through grounding in "physical" substrate.

    "Consciousness is not just in the head - it is in the body."
    """

    def __init__(
        self, config: InteroceptionConfig | None = None, monitor_id: str = "mmei-monitor-primary"
    ):
        self.monitor_id = monitor_id
        self.config = config or InteroceptionConfig()

        # State
        self._running: bool = False
        self._monitoring_task: asyncio.Task | None = None

        # Metrics history
        self._metrics_history: list[PhysicalMetrics] = []
        self._needs_history: list[AbstractNeeds] = []

        # Current state
        self._current_metrics: PhysicalMetrics | None = None
        self._current_needs: AbstractNeeds | None = None

        # Metrics collection
        self._metrics_collector: (
            Callable[[], PhysicalMetrics | Coroutine[Any, Any, PhysicalMetrics]] | None
        ) = None

        # Callbacks
        self._need_callbacks: list[tuple[Callable, float]] = []  # (callback, threshold)

        # Performance tracking
        self.total_collections: int = 0
        self.failed_collections: int = 0
        self.callback_invocations: int = 0

        # Needs computation engine
        self.needs_computation = NeedsComputation(self.config)

        # FASE VII (Safety Hardening): Goal management & overflow protection
        self.goal_manager = GoalManager()

    def set_metrics_collector(
        self, collector: Callable[[], PhysicalMetrics | Coroutine[Any, Any, PhysicalMetrics]]
    ) -> None:
        """
        Set the metrics collection function.

        The collector should return PhysicalMetrics with current system state.
        Can be sync or async function.

        Args:
            collector: Function returning PhysicalMetrics
        """
        self._metrics_collector = collector

    def register_need_callback(
        self,
        callback: Callable[[AbstractNeeds], None | Coroutine[Any, Any, None]],
        threshold: float = 0.80,
    ) -> None:
        """
        Register callback invoked when any need exceeds threshold.

        Args:
            callback: Async function to call with AbstractNeeds
            threshold: Need value that triggers callback (0-1)
        """
        self._need_callbacks.append((callback, threshold))

    async def start(self) -> None:
        """Start continuous interoception monitoring."""
        if self._running:
            return

        if not self._metrics_collector:
            raise RuntimeError("No metrics collector set. Call set_metrics_collector() first.")

        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())

        logger.info("🧠 MMEI Monitor %s started (interoception active)", self.monitor_id)

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

        logger.info("🛑 MMEI Monitor %s stopped", self.monitor_id)

    async def _monitoring_loop(self) -> None:
        """
        Continuous monitoring loop.

        Collects metrics, computes needs, invokes callbacks.
        Runs at configured interval (~10 Hz default).
        """
        interval = self.config.collection_interval_ms / 1000.0

        while self._running:
            try:
                cycle_start = time.time()

                # Collect metrics
                metrics = await self._collect_metrics()

                if metrics:
                    # Store in history
                    self._metrics_history.append(metrics)
                    if len(self._metrics_history) > self.config.long_term_window_samples:
                        self._metrics_history.pop(0)

                    self._current_metrics = metrics

                    # Compute needs
                    needs = self._compute_needs(metrics)

                    # Store in history
                    self._needs_history.append(needs)
                    if len(self._needs_history) > self.config.long_term_window_samples:
                        self._needs_history.pop(0)

                    self._current_needs = needs

                    # Invoke callbacks if thresholds exceeded
                    await self._invoke_callbacks(needs)

                    self.total_collections += 1

                # Sleep until next cycle
                cycle_duration = time.time() - cycle_start
                sleep_time = max(0, interval - cycle_duration)
                await asyncio.sleep(sleep_time)

            except Exception as e:
                self.failed_collections += 1
                logger.info("⚠️  MMEI collection error: %s", e)
                await asyncio.sleep(interval)

    async def _collect_metrics(self) -> PhysicalMetrics | None:
        """Collect current physical metrics."""
        try:
            start = time.time()

            # Call collector (may be sync or async)
            if asyncio.iscoroutinefunction(self._metrics_collector):
                metrics = await self._metrics_collector()
            else:
                metrics = self._metrics_collector()

            # Record collection latency
            metrics.collection_latency_ms = (time.time() - start) * 1000.0

            # Normalize percentages
            return metrics.normalize()

        except Exception as e:
            self.failed_collections += 1
            logger.info("⚠️  Metrics collection failed: %s", e)
            return None

    def _compute_needs(self, metrics: PhysicalMetrics) -> AbstractNeeds:
        """
        Translate physical metrics to abstract needs.

        Delegates to NeedsComputation for implementation.

        Args:
            metrics: Current PhysicalMetrics

        Returns:
            AbstractNeeds computed from metrics
        """
        return self.needs_computation.compute_needs(metrics)

    async def _invoke_callbacks(self, needs: AbstractNeeds) -> None:
        """Invoke registered callbacks if thresholds exceeded."""
        # Check if any need exceeds any callback threshold
        max_need = max(
            [
                needs.rest_need,
                needs.repair_need,
                needs.efficiency_need,
                needs.connectivity_need,
            ]
        )

        for callback, threshold in self._need_callbacks:
            if max_need >= threshold:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(needs)
                    else:
                        callback(needs)

                    self.callback_invocations += 1

                except Exception as e:
                    logger.info("⚠️  Need callback error: %s", e)

    def get_current_needs(self) -> AbstractNeeds | None:
        """Get most recent computed needs."""
        return self._current_needs

    def get_current_metrics(self) -> PhysicalMetrics | None:
        """Get most recent collected metrics."""
        return self._current_metrics

    def get_needs_trend(self, need_name: str, window_samples: int | None = None) -> list[float]:
        """
        Get historical trend for specific need.

        Args:
            need_name: Name of need (e.g., "rest_need")
            window_samples: Number of samples to retrieve (None = all)

        Returns:
            List of need values in chronological order
        """
        if window_samples is None:
            history = self._needs_history
        else:
            history = self._needs_history[-window_samples:]

        return [getattr(needs, need_name, 0.0) for needs in history]

    def get_moving_average(self, need_name: str, window_samples: int | None = None) -> float:
        """
        Get moving average of specific need.

        Args:
            need_name: Name of need
            window_samples: Window size (None = use short_term_window)

        Returns:
            Average need value over window
        """
        if window_samples is None:
            window_samples = self.config.short_term_window_samples

        trend = self.get_needs_trend(need_name, window_samples)

        if not trend:
            return 0.0

        return float(np.mean(trend))

    def get_statistics(self) -> dict[str, any]:
        """Get monitor performance statistics."""
        success_rate = (
            (self.total_collections - self.failed_collections) / self.total_collections
            if self.total_collections > 0
            else 0.0
        )

        return {
            "monitor_id": self.monitor_id,
            "running": self._running,
            "total_collections": self.total_collections,
            "failed_collections": self.failed_collections,
            "success_rate": success_rate,
            "callback_invocations": self.callback_invocations,
            "history_samples": len(self._metrics_history),
            "current_needs": self._current_needs,
        }

    # ========================================================================
    # FASE VII (Safety Hardening): Goal Generation & Overflow Protection
    # ========================================================================

    def generate_goal_from_need(
        self,
        need_name: str,
        need_value: float,
        urgency: NeedUrgency,
    ) -> Goal | None:
        """
        Generate a goal from an abstract need with full safety checks.

        Delegates to GoalManager for implementation.

        Args:
            need_name: Name of need (e.g., "rest_need")
            need_value: Need value [0-1]
            urgency: Computed urgency level

        Returns:
            Goal object if generated successfully, None if blocked by safety
        """
        return self.goal_manager.generate_goal_from_need(need_name, need_value, urgency)

    def mark_goal_executed(self, goal_id: str) -> bool:
        """
        Mark a goal as executed and remove from active goals.

        Args:
            goal_id: ID of goal to mark executed

        Returns:
            True if goal found and marked, False otherwise
        """
        return self.goal_manager.mark_goal_executed(goal_id)

    def get_health_metrics(self) -> dict[str, any]:
        """
        Get MMEI health metrics for Safety Core integration.

        Returns metrics about goal generation, rate limiting, overflow events,
        and current need state. Used by Safety Core for monitoring.

        Returns:
            Dict with health metrics
        """
        current_needs = self._current_needs
        goal_metrics = self.goal_manager.get_health_metrics()

        return {
            "monitor_id": self.monitor_id,
            "running": self._running,
            # Collection metrics
            "total_collections": self.total_collections,
            "failed_collections": self.failed_collections,
            "success_rate": (
                (self.total_collections - self.failed_collections) / self.total_collections
                if self.total_collections > 0
                else 0.0
            ),
            # Goal generation metrics (from goal_manager)
            **goal_metrics,
            # Current needs state
            "current_needs": {
                "rest_need": current_needs.rest_need if current_needs else 0.0,
                "repair_need": current_needs.repair_need if current_needs else 0.0,
                "efficiency_need": current_needs.efficiency_need if current_needs else 0.0,
                "connectivity_need": current_needs.connectivity_need if current_needs else 0.0,
                "most_urgent": (current_needs.get_most_urgent()[0] if current_needs else None),
            },
        }

    def __repr__(self) -> str:
        status = "RUNNING" if self._running else "STOPPED"
        needs_str = repr(self._current_needs) if self._current_needs else "None"
        return (
            f"InternalStateMonitor({self.monitor_id}, status={status}, "
            f"collections={self.total_collections}, needs={needs_str})"
        )
