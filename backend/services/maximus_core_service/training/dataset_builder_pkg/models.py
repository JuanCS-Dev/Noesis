"""Models for dataset builder module."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import numpy as np


class SplitStrategy(Enum):
    """Dataset split strategies."""

    RANDOM = "random"
    STRATIFIED = "stratified"
    TEMPORAL = "temporal"
    K_FOLD = "k_fold"


@dataclass
class DatasetSplit:
    """Represents a dataset split (train/val/test)."""

    name: str
    features: np.ndarray
    labels: np.ndarray
    sample_ids: list[str]
    indices: np.ndarray

    def __len__(self) -> int:
        return len(self.features)

    def __repr__(self) -> str:
        label_dist = np.bincount(self.labels[self.labels >= 0])
        return f"DatasetSplit(name={self.name}, size={len(self)}, label_dist={label_dist.tolist()})"

    def get_class_distribution(self) -> dict[int, int]:
        """Get class distribution."""
        unique, counts = np.unique(self.labels[self.labels >= 0], return_counts=True)
        return dict(zip(unique.tolist(), counts.tolist(), strict=False))

    def save(self, output_path: Path) -> None:
        """Save split to file."""
        import logging
        logger = logging.getLogger(__name__)
        
        np.savez_compressed(
            output_path,
            features=self.features,
            labels=self.labels,
            sample_ids=self.sample_ids,
            indices=self.indices,
        )
        logger.info("Saved %s split to %s", self.name, output_path)

    @classmethod
    def load(cls, filepath: Path, name: str = "split") -> DatasetSplit:
        """Load split from file."""
        data = np.load(filepath, allow_pickle=True)
        return cls(
            name=name,
            features=data["features"],
            labels=data["labels"],
            sample_ids=data["sample_ids"].tolist(),
            indices=data["indices"],
        )
