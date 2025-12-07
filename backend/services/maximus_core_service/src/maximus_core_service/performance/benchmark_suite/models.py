"""Benchmark Data Models.

Data classes for benchmark metrics and results.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkMetrics:
    """Metrics from a single benchmark run."""

    # Latency metrics (milliseconds)
    mean_latency: float
    median_latency: float
    p95_latency: float
    p99_latency: float
    min_latency: float
    max_latency: float
    std_latency: float

    # Throughput metrics
    throughput_samples_per_sec: float
    throughput_batches_per_sec: float

    # Memory metrics (MB)
    peak_memory_mb: float | None = None
    avg_memory_mb: float | None = None

    # GPU metrics (if available)
    gpu_utilization_percent: float | None = None
    gpu_memory_mb: float | None = None

    # Additional info
    batch_size: int = 1
    num_iterations: int = 100
    device: str = "cpu"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "latency": {
                "mean_ms": self.mean_latency,
                "median_ms": self.median_latency,
                "p95_ms": self.p95_latency,
                "p99_ms": self.p99_latency,
                "min_ms": self.min_latency,
                "max_ms": self.max_latency,
                "std_ms": self.std_latency,
            },
            "throughput": {
                "samples_per_sec": self.throughput_samples_per_sec,
                "batches_per_sec": self.throughput_batches_per_sec,
            },
            "memory": {
                "peak_mb": self.peak_memory_mb,
                "avg_mb": self.avg_memory_mb,
            },
            "gpu": {
                "utilization_percent": self.gpu_utilization_percent,
                "memory_mb": self.gpu_memory_mb,
            },
            "config": {
                "batch_size": self.batch_size,
                "num_iterations": self.num_iterations,
                "device": self.device,
            },
        }


@dataclass
class BenchmarkResult:
    """Complete benchmark results."""

    model_name: str
    timestamp: datetime
    metrics: BenchmarkMetrics
    hardware_info: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "model_name": self.model_name,
            "timestamp": self.timestamp.isoformat(),
            "metrics": self.metrics.to_dict(),
            "hardware_info": self.hardware_info,
        }

    def save(self, output_path: Path) -> None:
        """Save results to JSON file.

        Args:
            output_path: Path to save results.
        """
        with open(output_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

        logger.info("Benchmark results saved to %s", output_path)
