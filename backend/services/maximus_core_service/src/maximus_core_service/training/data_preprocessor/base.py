"""Base Preprocessor Interface.

Abstract base class for layer-specific preprocessing.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .models import LayerType, PreprocessedSample


class LayerPreprocessor(ABC):
    """Abstract base class for layer-specific preprocessing.

    Attributes:
        layer: Target layer type for this preprocessor.
    """

    def __init__(self, layer: LayerType) -> None:
        """Initialize preprocessor.

        Args:
            layer: Target layer type.
        """
        self.layer = layer

    @abstractmethod
    def preprocess(self, event: dict[str, Any]) -> PreprocessedSample:
        """Preprocess event for this layer.

        Args:
            event: Raw event data.

        Returns:
            Preprocessed sample.
        """

    @abstractmethod
    def get_feature_dim(self) -> int:
        """Get feature dimensionality for this layer.

        Returns:
            Feature dimension.
        """
