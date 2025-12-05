"""Distributed Training Package."""

from __future__ import annotations

from ..distributed_trainer_legacy import (
    DistributedConfig,
    DistributedTrainer,
    get_rank,
    get_world_size,
    is_dist_available_and_initialized,
    setup_for_distributed,
)

__all__ = [
    "DistributedTrainer",
    "DistributedConfig",
    "setup_for_distributed",
    "get_rank",
    "get_world_size",
    "is_dist_available_and_initialized",
]
