"""MetricsSPM - Internal metrics monitor for conscious self-awareness."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from typing import Any

from consciousness.esgt.coordinator import SalienceScore
from consciousness.esgt.spm.base import (
    ProcessingPriority,
    SpecializedProcessingModule,
    SPMOutput,
    SPMType,
)
from consciousness.esgt.spm.metrics_monitor_models import (
    MetricCategory,  # Re-exported for backward compatibility
    MetricsMonitorConfig,
    MetricsSnapshot,
)

__all__ = ["MetricsSPM", "MetricCategory", "MetricsMonitorConfig", "MetricsSnapshot"]
from consciousness.mmei.monitor import InternalStateMonitor


class MetricsSPM(SpecializedProcessingModule):
    """SPM for internal metrics monitoring and interoceptive self-awareness."""

    def __init__(
        self,
        spm_id: str,
        config: MetricsMonitorConfig | None = None,
        mmei_monitor: InternalStateMonitor | None = None,
    ) -> None:
        """Initialize MetricsSPM."""
        super().__init__(spm_id, SPMType.METACOGNITIVE)

        self.config = config or MetricsMonitorConfig()
        self.mmei_monitor = mmei_monitor

        self._running: bool = False
        self._monitoring_task: asyncio.Task | None = None

        self._snapshots: list[MetricsSnapshot] = []
        self._last_report_time: float = 0.0

        self._output_callbacks: list[Callable[[SPMOutput], None]] = []

        self.total_snapshots: int = 0
        self.high_salience_reports: int = 0

    async def start(self) -> None:
        """Start metrics monitoring."""
        if self._running:
            return

        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())

    async def stop(self) -> None:
        """Stop metrics monitoring."""
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
        """Continuous monitoring loop - collects metrics and generates outputs."""
        interval_s = self.config.monitoring_interval_ms / 1000.0

        while self._running:
            try:
                snapshot = await self._collect_snapshot()
                self.total_snapshots += 1

                self._snapshots.append(snapshot)
                if len(self._snapshots) > 100:
                    self._snapshots.pop(0)

                should_report = self._should_generate_report(snapshot)

                if should_report:
                    output = self._generate_output(snapshot)
                    self._dispatch_output(output)

                await asyncio.sleep(interval_s)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.info("[MetricsSPM %s] Monitoring error: {e}", self.spm_id)
                await asyncio.sleep(interval_s)

    async def _collect_snapshot(self) -> MetricsSnapshot:
        """Collect current metrics snapshot."""
        snapshot = MetricsSnapshot(timestamp=time.time())

        try:
            import psutil

            snapshot.cpu_usage_percent = psutil.cpu_percent(interval=None)
            snapshot.memory_usage_percent = psutil.virtual_memory().percent
            snapshot.thread_count = len(psutil.Process().threads())
        except ImportError:
            snapshot.cpu_usage_percent = 45.0
            snapshot.memory_usage_percent = 60.0
            snapshot.thread_count = 8

        if self.config.integrate_mmei and self.mmei_monitor:
            needs = self.mmei_monitor.get_current_needs()
            if needs:
                snapshot.needs = needs
                most_urgent, value, _ = needs.get_most_urgent()
                snapshot.most_urgent_need = most_urgent
                snapshot.most_urgent_value = value

        return snapshot

    def _should_generate_report(self, snapshot: MetricsSnapshot) -> bool:
        """Determine if current snapshot warrants a report."""
        min_interval = 1.0 / self.config.max_report_frequency_hz
        if time.time() - self._last_report_time < min_interval:
            return False

        if snapshot.cpu_usage_percent >= self.config.high_cpu_threshold * 100:
            return True

        if snapshot.memory_usage_percent >= self.config.high_memory_threshold * 100:
            return True

        if snapshot.error_rate_per_min >= self.config.high_error_rate_threshold:
            return True

        if snapshot.most_urgent_value >= self.config.critical_need_threshold:
            return True

        if self.config.report_significant_changes and len(self._snapshots) >= 2:
            prev = self._snapshots[-2]

            cpu_change = abs(snapshot.cpu_usage_percent - prev.cpu_usage_percent) / 100.0
            if cpu_change >= self.config.change_threshold:
                return True

            mem_change = abs(snapshot.memory_usage_percent - prev.memory_usage_percent) / 100.0
            if mem_change >= self.config.change_threshold:
                return True

            if prev.needs and snapshot.needs:
                need_change = abs(snapshot.most_urgent_value - prev.most_urgent_value)
                if need_change >= self.config.change_threshold:
                    return True

        if self.config.enable_continuous_reporting:
            return True

        return False

    def _generate_output(self, snapshot: MetricsSnapshot) -> SPMOutput:
        """Generate SPM output from snapshot."""
        salience = self._compute_salience(snapshot)
        priority = self._determine_priority(snapshot, salience)

        content = snapshot.to_dict()
        content["spm_type"] = "metrics_monitor"
        content["self_awareness"] = True

        output = SPMOutput(
            spm_id=self.spm_id,
            spm_type=self.spm_type,
            content=content,
            salience=salience,
            priority=priority,
            timestamp=snapshot.timestamp,
            confidence=1.0,
        )

        self._last_report_time = time.time()

        if salience.compute_total() >= 0.70:
            self.high_salience_reports += 1

        return output

    def _compute_salience(self, snapshot: MetricsSnapshot) -> SalienceScore:
        """Compute salience of metrics snapshot."""
        cpu_novelty = max(0.0, (snapshot.cpu_usage_percent - 60.0) / 40.0)
        mem_novelty = max(0.0, (snapshot.memory_usage_percent - 60.0) / 40.0)
        error_novelty = min(
            1.0, snapshot.error_rate_per_min / self.config.high_error_rate_threshold
        )

        novelty = min(1.0, max(cpu_novelty, mem_novelty, error_novelty))

        relevance = 0.5
        if snapshot.needs:
            max_need = snapshot.most_urgent_value
            relevance = min(1.0, 0.3 + max_need * 0.7)

        urgency = 0.2
        if snapshot.error_rate_per_min > 0:
            urgency = min(1.0, 0.2 + snapshot.error_rate_per_min / 10.0)

        if snapshot.cpu_usage_percent >= 95.0:
            urgency = max(urgency, 0.8)

        return SalienceScore(novelty=novelty, relevance=relevance, urgency=urgency)

    def _determine_priority(
        self,
        snapshot: MetricsSnapshot,
        salience: SalienceScore,
    ) -> ProcessingPriority:
        """Determine processing priority."""
        total_salience = salience.compute_total()

        if total_salience >= 0.90:
            return ProcessingPriority.CRITICAL

        if total_salience >= 0.70:
            return ProcessingPriority.FOCAL

        if total_salience >= 0.40:
            return ProcessingPriority.PERIPHERAL

        return ProcessingPriority.BACKGROUND

    def _dispatch_output(self, output: SPMOutput) -> None:
        """Dispatch output to registered callbacks."""
        for callback in self._output_callbacks:
            try:
                callback(output)
            except Exception as e:
                logger.info("[MetricsSPM %s] Callback error: {e}", self.spm_id)

    async def process(self) -> SPMOutput | None:
        """Process and generate output (required by base class)."""
        snapshot = await self._collect_snapshot()
        return self._generate_output(snapshot)

    def compute_salience(self, data: dict[str, Any]) -> SalienceScore:
        """Compute salience for given data (required by base class)."""
        snapshot = MetricsSnapshot(
            timestamp=time.time(),
            cpu_usage_percent=data.get("cpu_usage_percent", 50.0),
            memory_usage_percent=data.get("memory_usage_percent", 50.0),
            error_rate_per_min=data.get("error_rate_per_min", 0.0),
        )

        return self._compute_salience(snapshot)

    def register_output_callback(self, callback: Callable[[SPMOutput], None]) -> None:
        """Register callback for output events."""
        if callback not in self._output_callbacks:
            self._output_callbacks.append(callback)

    def get_current_snapshot(self) -> MetricsSnapshot | None:
        """Get most recent snapshot."""
        return self._snapshots[-1] if self._snapshots else None

    def get_metrics(self) -> dict[str, Any]:
        """Get SPM performance metrics."""
        return {
            "spm_id": self.spm_id,
            "running": self._running,
            "total_snapshots": self.total_snapshots,
            "high_salience_reports": self.high_salience_reports,
            "mmei_integrated": self.mmei_monitor is not None,
        }

    def __repr__(self) -> str:
        return (
            f"MetricsSPM(id={self.spm_id}, snapshots={self.total_snapshots}, "
            f"high_salience={self.high_salience_reports}, running={self._running})"
        )
