"""Inference Engine Configuration.

Configuration dataclass for inference settings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

# Try to import PyTorch for device detection
try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    if TYPE_CHECKING:
        import torch


@dataclass
class InferenceConfig:
    """Inference engine configuration.

    Attributes:
        backend: Inference backend (pytorch, onnx, tensorrt).
        device: Device to run inference on.
        max_batch_size: Maximum batch size.
        auto_batching: Enable auto-batching.
        batch_timeout_ms: Max wait time for batch.
        enable_cache: Enable result caching.
        max_cache_size: Maximum cache size.
        use_amp: Use Automatic Mixed Precision.
        compile_model: Use torch.compile.
        num_warmup_runs: Number of warmup runs.
        enable_profiling: Enable profiling.
        num_threads: Number of threads.
    """

    backend: str = "pytorch"
    device: str = "cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu"
    max_batch_size: int = 32
    auto_batching: bool = True
    batch_timeout_ms: float = 50.0
    enable_cache: bool = True
    max_cache_size: int = 1000
    use_amp: bool = True
    compile_model: bool = True
    num_warmup_runs: int = 10
    enable_profiling: bool = False
    num_threads: int = 4
