"""CLI for Inference Engine.

Command-line interface for running inference.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

from .config import InferenceConfig
from .engine import InferenceEngine

# Try to import PyTorch
try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    if TYPE_CHECKING:
        import torch

logger = logging.getLogger(__name__)


def main() -> None:
    """Main inference script."""
    import argparse

    parser = argparse.ArgumentParser(description="MAXIMUS Inference Engine")

    parser.add_argument("--model_path", type=str, required=True, help="Path to model")
    parser.add_argument(
        "--backend",
        type=str,
        default="pytorch",
        choices=["pytorch", "onnx", "tensorrt"],
        help="Inference backend",
    )
    parser.add_argument("--device", type=str, default="cuda", help="Device (cuda/cpu)")
    parser.add_argument("--batch_size", type=int, default=32, help="Max batch size")
    parser.add_argument(
        "--enable_cache", action="store_true", help="Enable result caching"
    )
    parser.add_argument(
        "--num_warmup", type=int, default=10, help="Number of warmup runs"
    )

    args = parser.parse_args()

    # Load model
    if args.backend == "pytorch":
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch not available")
        model = torch.load(args.model_path)
    else:
        model = args.model_path

    # Create engine
    config = InferenceConfig(
        backend=args.backend,
        device=args.device,
        max_batch_size=args.batch_size,
        enable_cache=args.enable_cache,
        num_warmup_runs=args.num_warmup,
    )

    engine = InferenceEngine(model=model, config=config)

    # Test inference
    if args.backend == "pytorch" and TORCH_AVAILABLE:
        dummy_input = torch.randn(1, 3, 224, 224)
    else:
        dummy_input = np.random.randn(1, 3, 224, 224).astype(np.float32)

    output = engine.predict(dummy_input)
    output_shape = output.shape if hasattr(output, "shape") else type(output)
    print(f"Output shape: {output_shape}")

    # Print stats
    stats = engine.get_stats()
    print("\nInference Stats:")
    print(f"  Total inferences: {stats['total_inferences']}")
    print(f"  Avg latency: {stats['avg_latency_ms']:.2f} ms")

    if "cache" in stats:
        print(f"  Cache hit rate: {stats['cache']['hit_rate']:.1%}")


if __name__ == "__main__":
    main()
