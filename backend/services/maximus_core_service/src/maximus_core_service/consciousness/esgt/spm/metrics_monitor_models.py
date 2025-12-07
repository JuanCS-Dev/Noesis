"""MetricsSPM Models - Data structures for internal metrics monitoring."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from consciousness.mmei.monitor import AbstractNeeds


class MetricCategory(Enum):
    """Categories of metrics monitored."""

    COMPUTATIONAL = "computational"  # CPU, memory, threads
    INTEROCEPTIVE = "interoceptive"  # Needs from MMEI
    PERFORMANCE = "performance"  # Latency, throughput
    HEALTH = "health"  # Errors, warnings
    RESOURCES = "resources"  # Disk, network


@dataclass
class MetricsMonitorConfig:
    """Configuration for metrics monitoring."""

    monitoring_interval_ms: float = 200.0  # 5 Hz sampling
    enable_continuous_reporting: bool = True

    # Salience thresholds
    high_cpu_threshold: float = 0.80
    high_memory_threshold: float = 0.75
    high_error_rate_threshold: float = 5.0
    critical_need_threshold: float = 0.80

    # MMEI integration
    integrate_mmei: bool = True
    mmei_poll_interval_ms: float = 100.0

    # Reporting
    report_significant_changes: bool = True
    change_threshold: float = 0.15
    max_report_frequency_hz: float = 2.0


@dataclass
class MetricsSnapshot:
    """Snapshot of system metrics at a point in time."""

    timestamp: float

    # Computational
    cpu_usage_percent: float = 0.0
    memory_usage_percent: float = 0.0
    thread_count: int = 0

    # Interoceptive (from MMEI)
    needs: AbstractNeeds | None = None
    most_urgent_need: str = "none"
    most_urgent_value: float = 0.0

    # Performance
    avg_latency_ms: float = 0.0

    # Health
    error_rate_per_min: float = 0.0
    warning_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "timestamp": self.timestamp,
            "cpu_usage_percent": self.cpu_usage_percent,
            "memory_usage_percent": self.memory_usage_percent,
            "thread_count": self.thread_count,
            "avg_latency_ms": self.avg_latency_ms,
            "error_rate_per_min": self.error_rate_per_min,
            "warning_count": self.warning_count,
            "most_urgent_need": self.most_urgent_need,
            "most_urgent_value": self.most_urgent_value,
        }

        if self.needs:
            result["needs"] = {
                "rest_need": self.needs.rest_need,
                "repair_need": self.needs.repair_need,
                "efficiency_need": self.needs.efficiency_need,
                "connectivity_need": self.needs.connectivity_need,
                "curiosity_drive": self.needs.curiosity_drive,
            }

        return result
