"""Models for FL storage module."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..base import ModelType


@dataclass
class ModelVersion:
    """Model version metadata."""

    version_id: int
    model_type: ModelType
    round_id: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    accuracy: float = 0.0
    total_parameters: int = 0
    file_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version_id": self.version_id,
            "model_type": self.model_type.value,
            "round_id": self.round_id,
            "timestamp": self.timestamp.isoformat(),
            "accuracy": self.accuracy,
            "total_parameters": self.total_parameters,
            "file_path": self.file_path,
            "metadata": self.metadata,
        }
