"""Pruning Models and Configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class PruningConfig:
    """Pruning configuration."""

    pruning_type: str = "unstructured"  # "unstructured", "structured"
    pruning_method: str = "l1"  # "l1", "random", "ln"
    target_sparsity: float = 0.5  # Target sparsity (0.0 to 1.0)
    iterative: bool = True
    num_iterations: int = 5
    finetune_epochs: int = 10
    skip_layers: list[str] | None = None
    output_dir: Path = Path("models/pruned")

    def __post_init__(self) -> None:
        """Validate configuration."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if self.skip_layers is None:
            self.skip_layers = []
        if not 0.0 <= self.target_sparsity <= 1.0:
            raise ValueError(f"target_sparsity must be in [0, 1], got {self.target_sparsity}")


@dataclass
class PruningResult:
    """Pruning result."""

    original_params: int
    pruned_params: int
    sparsity: float
    model_size_mb: float
    pruned_model_path: Path | None = None
    metadata: dict[str, Any] | None = None

    @property
    def compression_ratio(self) -> float:
        """Calculate compression ratio."""
        return 1.0 - (self.pruned_params / self.original_params) if self.original_params > 0 else 0.0
