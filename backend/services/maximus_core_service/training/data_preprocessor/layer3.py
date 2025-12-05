"""Layer 3 (Operational) Preprocessor - TCN Input.

Creates time series features:
- Sliding window of events (e.g., last 10 events)
- Temporal patterns
- Rate of events
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .base import LayerPreprocessor
from .layer1 import extract_label, generate_sample_id
from .models import LayerType, PreprocessedSample


class Layer3Preprocessor(LayerPreprocessor):
    """Preprocessor for Layer 3 (Operational) - TCN input.

    Attributes:
        window_size: Number of events in time window.
        event_feature_dim: Feature dimension per event (32).
        event_buffer: Buffer for sliding window.
    """

    def __init__(self, window_size: int = 10) -> None:
        """Initialize Layer 3 preprocessor.

        Args:
            window_size: Number of events in time window.
        """
        super().__init__(LayerType.LAYER3_OPERATIONAL)
        self.window_size = window_size
        self.event_feature_dim = 32
        self.event_buffer: list[np.ndarray] = []

    def preprocess(self, event: dict[str, Any]) -> PreprocessedSample:
        """Preprocess event for Layer 3.

        Args:
            event: Raw event data.

        Returns:
            Preprocessed sample with time series encoding.
        """
        event_features = self._extract_event_features(event)

        self.event_buffer.append(event_features)
        if len(self.event_buffer) > self.window_size:
            self.event_buffer = self.event_buffer[-self.window_size :]

        # Pad if needed
        features_list = self.event_buffer.copy()
        while len(features_list) < self.window_size:
            features_list.insert(0, np.zeros(self.event_feature_dim, dtype=np.float32))

        features = np.concatenate(features_list)

        label = extract_label(event)
        sample_id = generate_sample_id(event, "l3")

        return PreprocessedSample(
            sample_id=sample_id,
            layer=self.layer,
            features=features,
            label=label,
            metadata={"window_size": len(self.event_buffer)},
        )

    def get_feature_dim(self) -> int:
        """Get feature dimensionality.

        Returns:
            window_size * event_feature_dim (default: 320).
        """
        return self.window_size * self.event_feature_dim

    def _extract_event_features(self, event: dict[str, Any]) -> np.ndarray:
        """Extract features for a single event in time series.

        Args:
            event: Event data.

        Returns:
            32-dim event feature vector.
        """
        features = np.zeros(self.event_feature_dim, dtype=np.float32)

        event_types = [
            "network_connection",
            "process_creation",
            "file_creation",
            "authentication",
        ]
        event_type = event.get("type", "unknown")
        if event_type in event_types:
            features[event_types.index(event_type)] = 1.0

        if "timestamp" in event:
            timestamp = pd.to_datetime(event["timestamp"])
            features[10] = timestamp.hour / 24.0
            features[11] = timestamp.dayofweek / 7.0

        if "severity" in event:
            features[12] = event["severity"] / 10.0

        return features
