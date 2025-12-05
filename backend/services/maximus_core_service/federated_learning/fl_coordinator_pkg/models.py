"""Models for FL coordinator module."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field

from ..base import FLConfig


@dataclass
class CoordinatorConfig:
    """Configuration for FL coordinator."""

    fl_config: FLConfig
    max_rounds: int = 100
    convergence_threshold: float = 0.001
    min_improvement_rounds: int = 5
    evaluation_frequency: int = 1
    auto_save: bool = True
    save_directory: str = field(
        default_factory=lambda: os.getenv("FL_MODELS_DIR", tempfile.mkdtemp(prefix="fl_models_", suffix="_maximus"))
    )
