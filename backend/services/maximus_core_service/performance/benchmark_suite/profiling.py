"""Profiling Utilities.

Memory and GPU profiling functionality for benchmarks.
"""

from __future__ import annotations

import logging
from typing import Any

# Try to import psutil for system metrics
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)


class ProfilingMixin:
    """Mixin providing profiling capabilities.

    Provides memory and GPU profiling methods for benchmarks.
    """

    def _get_memory_usage(self) -> float | None:
        """Get current memory usage in MB.

        Returns:
            Memory usage in MB or None if unavailable.
        """
        if not PSUTIL_AVAILABLE:
            return None

        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)

    def _get_gpu_metrics(self) -> tuple[float | None, float | None]:
        """Get GPU utilization and memory.

        Returns:
            Tuple of (utilization_percent, memory_mb).
        """
        try:
            import torch

            if torch.cuda.is_available():
                utilization = torch.cuda.utilization()
                memory_allocated = torch.cuda.memory_allocated() / (1024 * 1024)
                return float(utilization), float(memory_allocated)

        except ImportError:
            logger.debug("PyTorch not available for GPU monitoring")
        except Exception as e:
            logger.debug("GPU monitoring failed: %s", e)

        return None, None

    def _prepare_model(self, model: Any, device: str) -> Any:
        """Prepare model for benchmarking.

        Args:
            model: Model to prepare.
            device: Target device.

        Returns:
            Prepared model.
        """
        try:
            import torch

            if hasattr(model, "eval"):
                model.eval()

            if hasattr(model, "to"):
                model = model.to(device)

            # Check gradient capability
            if hasattr(torch, "no_grad"):
                return model

        except ImportError:
            pass

        return model

    def _create_dummy_input(self, shape: tuple[int, ...], device: str) -> Any:
        """Create dummy input tensor.

        Args:
            shape: Input shape.
            device: Target device.

        Returns:
            Dummy input tensor.
        """
        try:
            import torch

            return torch.randn(shape, device=device)
        except ImportError:
            import numpy as np

            return np.random.randn(*shape).astype(np.float32)

    def _run_inference(self, model: Any, input_tensor: Any) -> Any:
        """Run inference on model.

        Args:
            model: Model to run.
            input_tensor: Input data.

        Returns:
            Model output.
        """
        try:
            import torch

            with torch.no_grad():
                output = model(input_tensor)

            # Synchronize for accurate timing
            if torch.cuda.is_available():
                torch.cuda.synchronize()

            return output

        except ImportError:
            # Fallback for non-PyTorch models
            if hasattr(model, "predict"):
                return model.predict(input_tensor)
            return model(input_tensor)
