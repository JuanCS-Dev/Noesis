"""Layer 1 (Sensory) Preprocessor - VAE Input.

Extracts low-level features:
- Network features (IPs, ports, protocols)
- Process features (PIDs, names, paths)
- File features (hashes, sizes, extensions)
- User features (UIDs, names, domains)
"""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np
import pandas as pd

from .base import LayerPreprocessor
from .models import LayerType, PreprocessedSample


class Layer1Preprocessor(LayerPreprocessor):
    """Preprocessor for Layer 1 (Sensory) - VAE input.

    Attributes:
        feature_dim: Fixed feature dimension (128).
        protocol_vocab: Protocol name to ID mapping.
        event_type_vocab: Event type to ID mapping.
    """

    def __init__(self) -> None:
        """Initialize Layer 1 preprocessor."""
        super().__init__(LayerType.LAYER1_SENSORY)
        self.feature_dim = 128
        self.protocol_vocab = {
            "tcp": 0, "udp": 1, "icmp": 2, "http": 3, "https": 4, "dns": 5
        }
        self.event_type_vocab = {
            "network_connection": 0,
            "process_creation": 1,
            "file_creation": 2,
            "registry_modification": 3,
            "authentication": 4,
        }

    def preprocess(self, event: dict[str, Any]) -> PreprocessedSample:
        """Preprocess event for Layer 1.

        Args:
            event: Raw event data.

        Returns:
            Preprocessed sample with 128-dim feature vector.
        """
        features = np.zeros(self.feature_dim, dtype=np.float32)

        # Extract event type (one-hot encoding)
        event_type = event.get("type", event.get("event_type", "unknown"))
        event_type_id = self.event_type_vocab.get(event_type, -1)
        if event_type_id >= 0:
            features[event_type_id] = 1.0

        # Network features (indices 10-30)
        self._extract_network_features(event, features)

        # Process features (indices 30-50)
        self._extract_process_features(event, features)

        # File features (indices 50-70)
        self._extract_file_features(event, features)

        # User features (indices 70-90)
        self._extract_user_features(event, features)

        # Timestamp features (indices 90-95)
        self._extract_timestamp_features(event, features)

        label = extract_label(event)
        sample_id = generate_sample_id(event, "l1")

        return PreprocessedSample(
            sample_id=sample_id,
            layer=self.layer,
            features=features,
            label=label,
            metadata={"event_type": event_type, "timestamp": event.get("timestamp")},
        )

    def get_feature_dim(self) -> int:
        """Get feature dimensionality.

        Returns:
            128 dimensions.
        """
        return self.feature_dim

    def _extract_network_features(
        self, event: dict[str, Any], features: np.ndarray
    ) -> None:
        """Extract network features into indices 10-30."""
        if "source_ip" in event:
            features[10:14] = encode_ip(event["source_ip"])
        if "dest_ip" in event:
            features[14:18] = encode_ip(event["dest_ip"])
        if "source_port" in event:
            features[18] = event["source_port"] / 65535.0
        if "dest_port" in event:
            features[19] = event["dest_port"] / 65535.0
        if "protocol" in event:
            protocol = event["protocol"].lower()
            protocol_id = self.protocol_vocab.get(protocol, -1)
            if protocol_id >= 0:
                features[20 + protocol_id] = 1.0

    def _extract_process_features(
        self, event: dict[str, Any], features: np.ndarray
    ) -> None:
        """Extract process features into indices 30-50."""
        if "process_name" in event:
            features[30:34] = encode_string(event["process_name"])
        if "process_pid" in event:
            features[34] = min(event["process_pid"] / 10000.0, 1.0)
        if "parent_process_name" in event:
            features[35:39] = encode_string(event["parent_process_name"])

    def _extract_file_features(
        self, event: dict[str, Any], features: np.ndarray
    ) -> None:
        """Extract file features into indices 50-70."""
        if "file_name" in event:
            features[50:54] = encode_string(event["file_name"])
        if "file_size" in event:
            features[54] = min(event["file_size"] / 1e9, 1.0)
        if "file_hash" in event:
            features[55:59] = encode_hash(event["file_hash"])

    def _extract_user_features(
        self, event: dict[str, Any], features: np.ndarray
    ) -> None:
        """Extract user features into indices 70-90."""
        if "user_name" in event:
            features[70:74] = encode_string(event["user_name"])
        if "user_domain" in event:
            features[74:78] = encode_string(event["user_domain"])

    def _extract_timestamp_features(
        self, event: dict[str, Any], features: np.ndarray
    ) -> None:
        """Extract timestamp features into indices 90-95."""
        if "timestamp" in event:
            timestamp = pd.to_datetime(event["timestamp"])
            features[90] = timestamp.hour / 24.0
            features[91] = timestamp.dayofweek / 7.0
            features[92] = timestamp.day / 31.0


def encode_ip(ip_str: str) -> np.ndarray:
    """Encode IP address to 4-dim vector.

    Args:
        ip_str: IP address string.

    Returns:
        Normalized 4-dim vector.
    """
    try:
        octets = [int(x) for x in ip_str.split(".")]
        return np.array(octets, dtype=np.float32) / 255.0
    except (ValueError, AttributeError):
        return np.zeros(4, dtype=np.float32)


def encode_string(s: str, dim: int = 4) -> np.ndarray:
    """Encode string to fixed-dim vector using hash.

    Args:
        s: Input string.
        dim: Output dimension.

    Returns:
        Encoded vector.
    """
    hash_bytes = hashlib.md5(s.encode()).digest()
    hash_ints = np.frombuffer(hash_bytes[: dim * 4], dtype=np.int32)
    return (hash_ints % 256).astype(np.float32) / 255.0


def encode_hash(hash_str: str, dim: int = 4) -> np.ndarray:
    """Encode hash (MD5/SHA256) to fixed-dim vector.

    Args:
        hash_str: Hash string.
        dim: Output dimension.

    Returns:
        Encoded vector.
    """
    try:
        hash_bytes = bytes.fromhex(hash_str[: dim * 8])
        hash_ints = np.frombuffer(hash_bytes[: dim * 4], dtype=np.int32)
        return (hash_ints % 256).astype(np.float32) / 255.0
    except (ValueError, AttributeError):
        return np.zeros(dim, dtype=np.float32)


def extract_label(event: dict[str, Any]) -> int | None:
    """Extract label from event.

    Args:
        event: Event data.

    Returns:
        Label (0=benign, 1=malicious) or None.
    """
    labels = event.get("labels", {})
    if isinstance(labels, dict):
        is_threat = labels.get("is_threat", labels.get("is_malicious"))
        if is_threat is not None:
            return 1 if is_threat else 0

    label_value = event.get("label")
    if label_value is not None:
        if isinstance(label_value, (int, np.integer)):
            return int(label_value)

        if isinstance(label_value, str):
            label_str = label_value.lower()
            if any(k in label_str for k in ("threat", "malicious", "attack")):
                return 1
            if any(k in label_str for k in ("normal", "benign")):
                return 0

    return None


def generate_sample_id(event: dict[str, Any], prefix: str) -> str:
    """Generate unique sample ID.

    Args:
        event: Event data.
        prefix: ID prefix (e.g., 'l1', 'l2').

    Returns:
        Sample ID.
    """
    event_id = event.get("id", event.get("event_id"))
    if event_id:
        return f"{prefix}_{event_id}"

    event_str = str(sorted(event.items()))
    hash_id = hashlib.sha256(event_str.encode()).hexdigest()[:16]
    return f"{prefix}_{hash_id}"
