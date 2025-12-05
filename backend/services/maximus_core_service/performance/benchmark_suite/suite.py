"""Benchmark Suite.

Main benchmarking functionality for MAXIMUS models.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import numpy as np

from .hardware import HardwareMixin
from .models import BenchmarkMetrics, BenchmarkResult
from .profiling import ProfilingMixin

logger = logging.getLogger(__name__)


class BenchmarkSuite(HardwareMixin, ProfilingMixin):
    """Comprehensive benchmarking suite for models.

    Features:
    - Latency measurement (warmup, multiple iterations)
    - Throughput calculation
    - Memory profiling
    - GPU utilization tracking
    - Multi-batch size testing
    - Comparative analysis

    Example:
        ```python
        import torch

        model = MyModel()
        suite = BenchmarkSuite()

        result = suite.benchmark_model(
            model=model,
            input_shape=(1, 128),
            batch_sizes=[1, 8, 32, 64],
            num_iterations=1000,
            device="cuda"
        )

        suite.print_report(result)
        result.save("benchmark_results.json")
        ```

    Attributes:
        results: List of benchmark results.
        hardware_info: Detected hardware information.
    """

    def __init__(self) -> None:
        """Initialize benchmark suite."""
        self.results: list[BenchmarkResult] = []
        self.hardware_info = self._get_hardware_info()
        logger.info("BenchmarkSuite initialized")

    def benchmark_model(
        self,
        model: Any,
        input_shape: tuple[int, ...],
        batch_sizes: list[int] | None = None,
        num_iterations: int = 1000,
        warmup_iterations: int = 100,
        device: str = "cpu",
    ) -> dict[int, BenchmarkMetrics]:
        """Benchmark model across multiple batch sizes.

        Args:
            model: Model to benchmark.
            input_shape: Input tensor shape (excluding batch dimension).
            batch_sizes: List of batch sizes to test.
            num_iterations: Number of iterations per batch size.
            warmup_iterations: Number of warmup iterations.
            device: Device to run on ("cpu" or "cuda").

        Returns:
            Dictionary mapping batch_size to BenchmarkMetrics.
        """
        if batch_sizes is None:
            batch_sizes = [1, 8, 32, 64]

        logger.info("Benchmarking model on %s with batch sizes %s", device, batch_sizes)

        model = self._prepare_model(model, device)
        results: dict[int, BenchmarkMetrics] = {}

        for batch_size in batch_sizes:
            logger.info("Benchmarking batch_size=%d", batch_size)

            metrics = self._benchmark_single_config(
                model=model,
                input_shape=input_shape,
                batch_size=batch_size,
                num_iterations=num_iterations,
                warmup_iterations=warmup_iterations,
                device=device,
            )

            results[batch_size] = metrics
            logger.info("  Mean latency: %.2f ms", metrics.mean_latency)
            logger.info("  Throughput: %.0f samples/sec", metrics.throughput_samples_per_sec)

        return results

    def _benchmark_single_config(
        self,
        model: Any,
        input_shape: tuple[int, ...],
        batch_size: int,
        num_iterations: int,
        warmup_iterations: int,
        device: str,
    ) -> BenchmarkMetrics:
        """Benchmark single configuration.

        Args:
            model: Model to benchmark.
            input_shape: Input shape.
            batch_size: Batch size.
            num_iterations: Number of iterations.
            warmup_iterations: Warmup iterations.
            device: Target device.

        Returns:
            Benchmark metrics for this configuration.
        """
        full_input_shape = (batch_size,) + input_shape
        dummy_input = self._create_dummy_input(full_input_shape, device)

        # Warmup
        logger.debug("Warmup: %d iterations", warmup_iterations)
        for _ in range(warmup_iterations):
            self._run_inference(model, dummy_input)

        # Benchmark
        latencies = []
        memory_usage = []

        for _ in range(num_iterations):
            mem_before = self._get_memory_usage()

            start = time.perf_counter()
            self._run_inference(model, dummy_input)
            end = time.perf_counter()

            mem_after = self._get_memory_usage()

            latency_ms = (end - start) * 1000
            latencies.append(latency_ms)

            if mem_before is not None and mem_after is not None:
                memory_usage.append(mem_after - mem_before)

        return self._compute_metrics(
            latencies=latencies,
            memory_usage=memory_usage,
            batch_size=batch_size,
            num_iterations=num_iterations,
            device=device,
        )

    def _compute_metrics(
        self,
        latencies: list[float],
        memory_usage: list[float],
        batch_size: int,
        num_iterations: int,
        device: str,
    ) -> BenchmarkMetrics:
        """Compute benchmark metrics from raw data.

        Args:
            latencies: List of latency measurements.
            memory_usage: List of memory usage measurements.
            batch_size: Batch size used.
            num_iterations: Number of iterations run.
            device: Device used.

        Returns:
            Computed benchmark metrics.
        """
        latencies_array = np.array(latencies)

        mean_latency = float(np.mean(latencies_array))
        median_latency = float(np.median(latencies_array))
        p95_latency = float(np.percentile(latencies_array, 95))
        p99_latency = float(np.percentile(latencies_array, 99))
        min_latency = float(np.min(latencies_array))
        max_latency = float(np.max(latencies_array))
        std_latency = float(np.std(latencies_array))

        throughput_samples_per_sec = (batch_size * 1000) / mean_latency
        throughput_batches_per_sec = 1000 / mean_latency

        peak_memory_mb = None
        avg_memory_mb = None
        if memory_usage:
            peak_memory_mb = float(max(memory_usage))
            avg_memory_mb = float(np.mean(memory_usage))

        gpu_utilization = None
        gpu_memory = None
        if device == "cuda":
            gpu_utilization, gpu_memory = self._get_gpu_metrics()

        return BenchmarkMetrics(
            mean_latency=mean_latency,
            median_latency=median_latency,
            p95_latency=p95_latency,
            p99_latency=p99_latency,
            min_latency=min_latency,
            max_latency=max_latency,
            std_latency=std_latency,
            throughput_samples_per_sec=throughput_samples_per_sec,
            throughput_batches_per_sec=throughput_batches_per_sec,
            peak_memory_mb=peak_memory_mb,
            avg_memory_mb=avg_memory_mb,
            gpu_utilization_percent=gpu_utilization,
            gpu_memory_mb=gpu_memory,
            batch_size=batch_size,
            num_iterations=num_iterations,
            device=device,
        )

    def compare_models(
        self,
        models: dict[str, Any],
        input_shape: tuple[int, ...],
        batch_size: int = 32,
        num_iterations: int = 1000,
        device: str = "cpu",
    ) -> dict[str, BenchmarkMetrics]:
        """Compare multiple models.

        Args:
            models: Dictionary mapping model_name to model.
            input_shape: Input shape.
            batch_size: Batch size to use.
            num_iterations: Number of iterations.
            device: Target device.

        Returns:
            Dictionary mapping model_name to BenchmarkMetrics.
        """
        logger.info("Comparing %d models", len(models))

        results: dict[str, BenchmarkMetrics] = {}

        for model_name, model in models.items():
            logger.info("Benchmarking %s", model_name)

            prepared_model = self._prepare_model(model, device)
            metrics = self._benchmark_single_config(
                model=prepared_model,
                input_shape=input_shape,
                batch_size=batch_size,
                num_iterations=num_iterations,
                warmup_iterations=100,
                device=device,
            )

            results[model_name] = metrics

        self.print_comparison(results)
        return results

    def print_report(self, results: dict[int, BenchmarkMetrics]) -> None:
        """Print benchmark report.

        Args:
            results: Benchmark results by batch size.
        """
        logger.info("=" * 80)
        logger.info("BENCHMARK REPORT")
        logger.info("=" * 80)

        logger.info("\nHardware:")
        for key, value in self.hardware_info.items():
            logger.info("  %s: {value}", key)

        logger.info("\nResults by Batch Size:")
        logger.info("-" * 80)
        logger.info("%8s %12s %12s %12s %20s", "Batch", "Mean(ms)", "P95(ms)", "P99(ms)", "Throughput(samp/s)")
        logger.info("-" * 80)

        for batch_size, metrics in sorted(results.items()):
            logger.info(
                "%8d %12.2f %12.2f %12.2f %20.0f",
                batch_size, metrics.mean_latency, metrics.p95_latency,
                metrics.p99_latency, metrics.throughput_samples_per_sec
            )

        logger.info("=" * 80)

    def print_comparison(self, results: dict[str, BenchmarkMetrics]) -> None:
        """Print model comparison.

        Args:
            results: Results dictionary by model name.
        """
        logger.info("=" * 80)
        logger.info("MODEL COMPARISON")
        logger.info("=" * 80)

        logger.info("\n%20s %20s %20s %15s", "Model", "Mean Latency(ms)", "Throughput(samp/s)", "Memory(MB)")
        logger.info("-" * 80)

        for model_name, metrics in sorted(
            results.items(), key=lambda x: x[1].mean_latency
        ):
            mem_str = (
                f"{metrics.peak_memory_mb:.1f}" if metrics.peak_memory_mb else "N/A"
            )
            logger.info(
                "%20s %20.2f %20.0f %15s",
                model_name, metrics.mean_latency,
                metrics.throughput_samples_per_sec, mem_str
            )

        logger.info("=" * 80)
