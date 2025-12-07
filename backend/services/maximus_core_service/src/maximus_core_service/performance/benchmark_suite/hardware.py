"""Hardware Detection.

Hardware information detection for benchmarks.
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


class HardwareMixin:
    """Mixin providing hardware detection capabilities.

    Provides methods for detecting CPU, GPU, and memory information.
    """

    def _get_hardware_info(self) -> dict[str, Any]:
        """Get hardware information.

        Returns:
            Hardware info dictionary.
        """
        info: dict[str, Any] = {}

        # CPU info
        if PSUTIL_AVAILABLE:
            info["cpu_count"] = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            info["cpu_freq_mhz"] = cpu_freq.current if cpu_freq else None
            info["total_memory_gb"] = psutil.virtual_memory().total / (1024**3)

        # GPU info
        info.update(self._get_gpu_info())

        return info

    def _get_gpu_info(self) -> dict[str, Any]:
        """Get GPU information.

        Returns:
            GPU info dictionary.
        """
        try:
            import torch

            if torch.cuda.is_available():
                return {
                    "gpu_available": True,
                    "gpu_count": torch.cuda.device_count(),
                    "gpu_name": torch.cuda.get_device_name(0),
                    "gpu_memory_gb": (
                        torch.cuda.get_device_properties(0).total_memory / (1024**3)
                    ),
                }
            return {"gpu_available": False}

        except ImportError:
            return {"gpu_available": False}
