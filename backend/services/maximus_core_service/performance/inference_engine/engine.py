"""Inference Engine.

Main inference engine class combining all functionality.
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from typing import TYPE_CHECKING, Any

import numpy as np

from .backends import BackendMixin
from .cache import LRUCache
from .config import InferenceConfig

# Try to import PyTorch
try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    if TYPE_CHECKING:
        import torch

logger = logging.getLogger(__name__)


class InferenceEngine(BackendMixin):
    """Optimized inference engine.

    Multi-backend support with caching, batching, and profiling.

    Attributes:
        config: Inference configuration.
        cache: LRU cache for results.
        model: Loaded model.
        total_inferences: Total inference count.
        total_latency_ms: Total latency in ms.
        lock: Thread lock.
    """

    def __init__(
        self,
        model: Any,
        config: InferenceConfig | None = None,
    ) -> None:
        """Initialize inference engine.

        Args:
            model: Model (PyTorch, ONNX, or TensorRT).
            config: Inference configuration.
        """
        self.config = config or InferenceConfig()
        self.cache = (
            LRUCache(max_size=self.config.max_cache_size)
            if self.config.enable_cache
            else None
        )

        self.total_inferences = 0
        self.total_latency_ms = 0.0
        self.lock = threading.Lock()

        self.model = self._setup_model(model)

        if self.config.num_warmup_runs > 0:
            self._warmup()

        logger.info(
            "InferenceEngine initialized: backend=%s, device=%s",
            self.config.backend,
            self.config.device,
        )

    def predict(self, input_data: Any) -> Any:
        """Run inference on single input.

        Args:
            input_data: Input tensor or array.

        Returns:
            Model output.
        """
        if self.cache is not None:
            cache_key = self._compute_cache_key(input_data)
            cached_result = self.cache.get(cache_key)

            if cached_result is not None:
                logger.debug("Cache hit")
                return cached_result

        start = time.perf_counter()
        output = self._run_inference(input_data)
        end = time.perf_counter()
        latency_ms = (end - start) * 1000

        with self.lock:
            self.total_inferences += 1
            self.total_latency_ms += latency_ms

        if self.cache is not None:
            self.cache.put(cache_key, output)

        return output

    def predict_batch(self, inputs: list[Any]) -> list[Any]:
        """Run inference on batch of inputs.

        Args:
            inputs: List of input tensors.

        Returns:
            List of outputs.
        """
        if not inputs:
            return []

        outputs = []
        batch_size = self.config.max_batch_size

        for i in range(0, len(inputs), batch_size):
            batch = inputs[i : i + batch_size]

            if self.config.backend == "pytorch" and TORCH_AVAILABLE:
                batch_tensor = torch.stack(
                    [
                        x if isinstance(x, torch.Tensor) else torch.tensor(x)
                        for x in batch
                    ]
                )
            else:
                batch_tensor = np.stack(batch)

            batch_outputs = self._run_inference(batch_tensor)

            if self.config.backend == "pytorch" and TORCH_AVAILABLE:
                outputs.extend(list(batch_outputs))
            else:
                outputs.extend([batch_outputs[j] for j in range(len(batch))])

        return outputs

    def _compute_cache_key(self, input_data: Any) -> str:
        """Compute cache key for input.

        Args:
            input_data: Input data.

        Returns:
            Cache key (hash).
        """
        if TORCH_AVAILABLE and isinstance(input_data, torch.Tensor):
            data_bytes = input_data.cpu().numpy().tobytes()
        elif isinstance(input_data, np.ndarray):
            data_bytes = input_data.tobytes()
        else:
            data_bytes = str(input_data).encode()

        return hashlib.md5(data_bytes).hexdigest()

    def get_stats(self) -> dict[str, Any]:
        """Get engine statistics.

        Returns:
            Statistics dictionary.
        """
        avg_latency = 0.0
        if self.total_inferences > 0:
            avg_latency = self.total_latency_ms / self.total_inferences

        stats = {
            "total_inferences": self.total_inferences,
            "avg_latency_ms": avg_latency,
            "backend": self.config.backend,
            "device": self.config.device,
        }

        if self.cache is not None:
            stats["cache"] = self.cache.get_stats()

        return stats

    def clear_cache(self) -> None:
        """Clear inference cache."""
        if self.cache is not None:
            self.cache.clear()
            logger.info("Cache cleared")

    def reset_stats(self) -> None:
        """Reset statistics."""
        with self.lock:
            self.total_inferences = 0
            self.total_latency_ms = 0.0

        if self.cache is not None:
            self.cache.hits = 0
            self.cache.misses = 0

        logger.info("Stats reset")
