"""Distributed Training Models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DistributedConfig:
    """Distributed training configuration."""
    
    backend: str = "nccl"
    world_size: int = 1
    rank: int = 0
    local_rank: int = 0
    master_addr: str = "localhost"
    master_port: str = "12355"
