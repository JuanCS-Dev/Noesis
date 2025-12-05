"""Data Preprocessor Models.

Core data structures for the preprocessing pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np


class LayerType(Enum):
    """Predictive Coding layers."""

    LAYER1_SENSORY = "layer1_sensory"
    LAYER2_BEHAVIORAL = "layer2_behavioral"
    LAYER3_OPERATIONAL = "layer3_operational"
    LAYER4_TACTICAL = "layer4_tactical"
    LAYER5_STRATEGIC = "layer5_strategic"


@dataclass
class PreprocessedSample:
    """Preprocessed sample for training.

    Attributes:
        sample_id: Unique identifier for the sample.
        layer: Target layer type.
        features: Feature vector as numpy array.
        label: Optional label (0=benign, 1=malicious).
        metadata: Optional metadata dictionary.
    """

    sample_id: str
    layer: LayerType
    features: np.ndarray
    label: int | None = None
    metadata: dict[str, Any] | None = None

    def __repr__(self) -> str:
        return (
            f"PreprocessedSample(layer={self.layer.value}, "
            f"features_shape={self.features.shape}, label={self.label})"
        )
