"""
HCL Monitor Service - Metrics Collector
=======================================

Core logic for collecting system and service metrics.
"""

import asyncio
from datetime import datetime
from typing import List

import psutil  # type: ignore[import-untyped]

from ..config import MonitorSettings
from ..models.metrics import SystemMetrics
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class SystemMetricsCollector:
    """
    Collects real-time operational metrics from the host system and Maximus services.
    """

    def __init__(self, settings: MonitorSettings):
        """
        Initialize the collector.

        Args:
            settings: Monitor settings
        """
        self.settings = settings
        self.is_collecting = False
        self.latest_metrics: SystemMetrics | None = None
        self.metrics_history: List[SystemMetrics] = []

        # Initialize psutil counters
        self.last_disk_io = psutil.disk_io_counters()
        self.last_net_io = psutil.net_io_counters()
        self.last_check_time = datetime.now()

    async def start_collection(self) -> None:
        """Starts the continuous metric collection loop."""
        if self.is_collecting:
            logger.warning("collection_already_running")
            return

        self.is_collecting = True
        logger.info("starting_metric_collection", interval=self.settings.collection_interval)

        while self.is_collecting:
            try:
                await self._collect_metrics_once()
            except Exception as e:  # pylint: disable=broad-except
                logger.error("metric_collection_failed", error=str(e))

            await asyncio.sleep(self.settings.collection_interval)

    async def stop_collection(self) -> None:
        """Stops the continuous metric collection loop."""
        self.is_collecting = False
        logger.info("stopping_metric_collection")

    def _get_disk_io_rates(self, time_delta: float) -> tuple[float, float]:
        """Calculate disk I/O rates."""
        current_disk_io = psutil.disk_io_counters()
        if current_disk_io and self.last_disk_io:
            read_rate = (
                current_disk_io.read_bytes - self.last_disk_io.read_bytes
            ) / time_delta
            write_rate = (
                current_disk_io.write_bytes - self.last_disk_io.write_bytes
            ) / time_delta
        else:
            read_rate = 0.0
            write_rate = 0.0
        self.last_disk_io = current_disk_io
        return read_rate, write_rate

    def _get_net_io_rates(self, time_delta: float) -> tuple[float, float]:
        """Calculate network I/O rates."""
        current_net_io = psutil.net_io_counters()
        if current_net_io and self.last_net_io:
            recv_rate = (
                current_net_io.bytes_recv - self.last_net_io.bytes_recv
            ) / time_delta
            sent_rate = (
                current_net_io.bytes_sent - self.last_net_io.bytes_sent
            ) / time_delta
        else:
            recv_rate = 0.0
            sent_rate = 0.0
        self.last_net_io = current_net_io
        return recv_rate, sent_rate

    async def _collect_metrics_once(self) -> None:
        """Collects a single snapshot of system and service metrics."""
        current_time = datetime.now()
        time_delta = (current_time - self.last_check_time).total_seconds()

        # Prevent division by zero
        if time_delta <= 0:
            return

        # OS-level metrics using psutil
        cpu_percent = psutil.cpu_percent(interval=None)
        memory_info = psutil.virtual_memory()
        memory_percent = memory_info.percent

        # I/O Rates
        disk_read_rate, disk_write_rate = self._get_disk_io_rates(time_delta)
        net_recv_rate, net_sent_rate = self._get_net_io_rates(time_delta)

        # Update last state
        self.last_check_time = current_time

        # Simulate service-level metrics
        service_status = {
            "maximus_core": "healthy",
            "chemical_sensing": "healthy",
            "visual_cortex": "degraded" if cpu_percent > 80 else "healthy",
        }
        avg_latency_ms = 50.0 + (cpu_percent / 2)
        error_rate = 0.01 + (cpu_percent / 1000)

        metrics = SystemMetrics(
            timestamp=current_time,
            cpu_usage=cpu_percent,
            memory_usage=memory_percent,
            disk_io_read_rate=disk_read_rate,
            disk_io_write_rate=disk_write_rate,
            network_io_recv_rate=net_recv_rate,
            network_io_sent_rate=net_sent_rate,
            avg_latency_ms=avg_latency_ms,
            error_rate=error_rate,
            service_status=service_status,
        )

        self.latest_metrics = metrics
        self.metrics_history.append(metrics)

        # Maintain history size
        if len(self.metrics_history) > self.settings.history_max_size:
            self.metrics_history.pop(0)

        logger.debug(
            "metrics_collected",
            cpu=cpu_percent,
            memory=memory_percent
        )

    def get_latest_metrics(self) -> SystemMetrics | None:
        """Returns the most recently collected system metrics."""
        return self.latest_metrics

    def get_metrics_history(self, limit: int = 10) -> List[SystemMetrics]:
        """Returns a history of collected system metrics."""
        return self.metrics_history[-limit:]
