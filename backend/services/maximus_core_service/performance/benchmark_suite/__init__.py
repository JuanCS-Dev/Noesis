"""Benchmark Suite Package.

Comprehensive performance benchmarking for MAXIMUS models.
"""

from __future__ import annotations

from .cli import main
from .hardware import HardwareMixin
from .models import BenchmarkMetrics, BenchmarkResult
from .profiling import ProfilingMixin
from .suite import BenchmarkSuite

__all__ = [
    "BenchmarkMetrics",
    "BenchmarkResult",
    "BenchmarkSuite",
    "HardwareMixin",
    "main",
    "ProfilingMixin",
]
