"""Core Distributed Trainer."""

from __future__ import annotations

import logging
from .models import DistributedConfig

logger = logging.getLogger(__name__)


class DistributedTrainer:
    """Distributed training for multi-GPU."""
    
    def __init__(self, config: DistributedConfig | None = None) -> None:
        """Initialize distributed trainer."""
        self.config = config or DistributedConfig()
        self.logger = logger
