"""CLI for Benchmark Suite.

Command-line interface for running benchmarks.
"""

from __future__ import annotations

import argparse
import logging
from datetime import datetime
from pathlib import Path

from .models import BenchmarkResult
from .suite import BenchmarkSuite

logger = logging.getLogger(__name__)


def main() -> None:
    """Main benchmark script."""
    parser = argparse.ArgumentParser(description="Benchmark MAXIMUS Models")

    parser.add_argument(
        "--model_path", type=str, required=True, help="Path to model checkpoint"
    )
    parser.add_argument(
        "--input_shape", type=str, default="128", help="Input shape (comma-separated)"
    )
    parser.add_argument(
        "--batch_sizes",
        type=str,
        default="1,8,32,64",
        help="Batch sizes (comma-separated)",
    )
    parser.add_argument(
        "--num_iterations", type=int, default=1000, help="Number of iterations"
    )
    parser.add_argument(
        "--device", type=str, default="cpu", help="Device (cpu/cuda)"
    )
    parser.add_argument(
        "--output", type=str, default="benchmark_results.json", help="Output file"
    )

    args = parser.parse_args()

    input_shape = tuple(int(x) for x in args.input_shape.split(","))
    batch_sizes = [int(x) for x in args.batch_sizes.split(",")]

    try:
        import torch

        model = torch.load(args.model_path)
    except Exception as e:
        logger.error("Failed to load model: %s", e)
        return

    suite = BenchmarkSuite()

    results = suite.benchmark_model(
        model=model,
        input_shape=input_shape,
        batch_sizes=batch_sizes,
        num_iterations=args.num_iterations,
        device=args.device,
    )

    suite.print_report(results)

    for batch_size, metrics in results.items():
        result = BenchmarkResult(
            model_name=Path(args.model_path).stem,
            timestamp=datetime.utcnow(),
            metrics=metrics,
            hardware_info=suite.hardware_info,
        )

        output_path = (
            Path(args.output).parent / f"{Path(args.output).stem}_bs{batch_size}.json"
        )
        result.save(output_path)


if __name__ == "__main__":
    main()
