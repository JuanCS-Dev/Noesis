"""Profiler Models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProfilerConfig:
    """Profiler configuration."""
    
    profile_memory: bool = True
    profile_cpu: bool = True
    profile_cuda: bool = True
    output_dir: str = "profiling_results"


@dataclass  
class ProfilingResult:
    """Profiling result."""
    
    cpu_time: float = 0.0
    cuda_time: float = 0.0
    memory_mb: float = 0.0
    metrics: dict[str, Any] = field(default_factory=dict)
