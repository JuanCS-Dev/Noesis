"""Main Data Preprocessor.

Coordinates layer-specific preprocessing.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

from .base import LayerPreprocessor
from .layer1 import Layer1Preprocessor
from .layer2 import Layer2Preprocessor
from .layer3 import Layer3Preprocessor
from .models import LayerType, PreprocessedSample

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """Main preprocessor that coordinates layer-specific preprocessing.

    Example:
        ```python
        preprocessor = DataPreprocessor(output_dir="training/data/preprocessed")

        # Preprocess for all layers
        samples = preprocessor.preprocess_event(event, layers="all")

        # Preprocess for specific layer
        sample = preprocessor.preprocess_event(event, layers=[LayerType.LAYER1_SENSORY])
        ```

    Attributes:
        output_dir: Directory for preprocessed data output.
        preprocessors: Dictionary of layer preprocessors.
    """

    def __init__(self, output_dir: Path | str | None = None) -> None:
        """Initialize preprocessor.

        Args:
            output_dir: Directory to save preprocessed data.
        """
        self.output_dir = (
            Path(output_dir) if output_dir else Path("training/data/preprocessed")
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.preprocessors: dict[LayerType, LayerPreprocessor] = {
            LayerType.LAYER1_SENSORY: Layer1Preprocessor(),
            LayerType.LAYER2_BEHAVIORAL: Layer2Preprocessor(),
            LayerType.LAYER3_OPERATIONAL: Layer3Preprocessor(),
        }

        logger.info(
            f"DataPreprocessor initialized with {len(self.preprocessors)} "
            "layer preprocessors"
        )

    def preprocess_event(
        self, event: dict[str, Any], layers: str | list[LayerType] = "all"
    ) -> PreprocessedSample | dict[LayerType, PreprocessedSample]:
        """Preprocess event for specified layers.

        Args:
            event: Raw event data.
            layers: Target layers ("all" or list of LayerType).

        Returns:
            Preprocessed sample(s).
        """
        target_layers: list[LayerType]
        if layers == "all":
            target_layers = list(self.preprocessors.keys())
        else:
            target_layers = layers  # type: ignore[assignment]

        if len(target_layers) == 1:
            preprocessor = self.preprocessors[target_layers[0]]
            return preprocessor.preprocess(event)

        samples = {}
        for layer in target_layers:
            preprocessor = self.preprocessors[layer]
            samples[layer] = preprocessor.preprocess(event)
        return samples

    def preprocess_batch(
        self, events: list[dict[str, Any]], layer: LayerType
    ) -> list[PreprocessedSample]:
        """Preprocess batch of events for a specific layer.

        Args:
            events: List of raw events.
            layer: Target layer.

        Returns:
            List of preprocessed samples.
        """
        preprocessor = self.preprocessors[layer]
        return [preprocessor.preprocess(event) for event in events]

    def save_samples(self, samples: list[PreprocessedSample], filename: str) -> Path:
        """Save preprocessed samples to file.

        Args:
            samples: List of preprocessed samples.
            filename: Output filename (without extension).

        Returns:
            Path to saved file.
        """
        output_path = self.output_dir / f"{filename}.npz"

        features_list = [sample.features for sample in samples]
        labels_list = [
            sample.label if sample.label is not None else -1 for sample in samples
        ]
        sample_ids = [sample.sample_id for sample in samples]

        features = np.stack(features_list)
        labels = np.array(labels_list)

        np.savez_compressed(
            output_path,
            features=features,
            labels=labels,
            sample_ids=sample_ids,
            layer=str(samples[0].layer.value) if samples else "",
        )

        logger.info(f"Saved {len(samples)} samples to {output_path}")
        return output_path

    def load_samples(self, filepath: Path) -> list[PreprocessedSample]:
        """Load preprocessed samples from file.

        Args:
            filepath: Path to .npz file.

        Returns:
            List of preprocessed samples.
        """
        data = np.load(filepath, allow_pickle=True)

        features = data["features"]
        labels = data["labels"]
        sample_ids = data["sample_ids"]
        layer_str = str(data["layer"])

        layer = LayerType(layer_str)

        samples = []
        for i, feature in enumerate(features):
            label = int(labels[i]) if labels[i] >= 0 else None
            sample = PreprocessedSample(
                sample_id=str(sample_ids[i]),
                layer=layer,
                features=feature,
                label=label,
            )
            samples.append(sample)

        logger.info(f"Loaded {len(samples)} samples from {filepath}")
        return samples
