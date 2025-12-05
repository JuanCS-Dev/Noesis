"""Core training implementation."""

from __future__ import annotations

import logging
from .models import TrainingConfig

logger = logging.getLogger(__name__)


class Trainer:
    """Trainer."""
    
    def __init__(self, config: TrainingConfig | None = None) -> None:
        """Initialize trainer."""
        self.config = config or TrainingConfig()
        self.logger = logger
