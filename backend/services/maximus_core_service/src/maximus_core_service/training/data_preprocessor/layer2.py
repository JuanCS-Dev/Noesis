"""Layer 2 (Behavioral) Preprocessor - GNN Input.

Constructs behavior graphs:
- Nodes: Entities (processes, files, IPs)
- Edges: Interactions (spawns, reads, connects)
- Node features: Entity attributes
- Edge features: Interaction types
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .base import LayerPreprocessor
from .layer1 import encode_string, extract_label, generate_sample_id
from .models import LayerType, PreprocessedSample


class Layer2Preprocessor(LayerPreprocessor):
    """Preprocessor for Layer 2 (Behavioral) - GNN input.

    Attributes:
        node_feature_dim: Node feature dimension (64).
        edge_feature_dim: Edge feature dimension (16).
    """

    def __init__(self) -> None:
        """Initialize Layer 2 preprocessor."""
        super().__init__(LayerType.LAYER2_BEHAVIORAL)
        self.node_feature_dim = 64
        self.edge_feature_dim = 16

    def preprocess(self, event: dict[str, Any]) -> PreprocessedSample:
        """Preprocess event for Layer 2.

        Creates a graph representation:
        - features[0:64]: Source node features
        - features[64:128]: Destination node features
        - features[128:144]: Edge features

        Args:
            event: Raw event data.

        Returns:
            Preprocessed sample with graph encoding.
        """
        total_dim = self.node_feature_dim * 2 + self.edge_feature_dim
        features = np.zeros(total_dim, dtype=np.float32)

        # Extract source node (process/user/IP)
        source_features = self._extract_entity_features(
            entity_type="source",
            entity_data={
                "name": event.get(
                    "process_name",
                    event.get("user_name", event.get("source_ip")),
                ),
                "id": event.get("process_pid", event.get("source_port")),
                "attributes": event.get("process_attributes", {}),
            },
        )
        features[0 : self.node_feature_dim] = source_features

        # Extract destination node (file/IP/service)
        dest_features = self._extract_entity_features(
            entity_type="destination",
            entity_data={
                "name": event.get("file_name", event.get("dest_ip")),
                "id": event.get("dest_port"),
                "attributes": event.get("file_attributes", {}),
            },
        )
        features[self.node_feature_dim : self.node_feature_dim * 2] = dest_features

        # Extract edge (interaction type)
        edge_features = self._extract_interaction_features(event)
        features[self.node_feature_dim * 2 :] = edge_features

        label = extract_label(event)
        sample_id = generate_sample_id(event, "l2")

        return PreprocessedSample(
            sample_id=sample_id,
            layer=self.layer,
            features=features,
            label=label,
            metadata={"event_type": event.get("type")},
        )

    def get_feature_dim(self) -> int:
        """Get feature dimensionality.

        Returns:
            144 dimensions (64+64+16).
        """
        return self.node_feature_dim * 2 + self.edge_feature_dim

    def _extract_entity_features(
        self, entity_type: str, entity_data: dict[str, Any]
    ) -> np.ndarray:
        """Extract node features for an entity.

        Args:
            entity_type: Entity type (source/destination).
            entity_data: Entity data.

        Returns:
            64-dim feature vector.
        """
        features = np.zeros(self.node_feature_dim, dtype=np.float32)

        name = entity_data.get("name", "")
        if name:
            features[0:4] = encode_string(name, dim=4)

        entity_id = entity_data.get("id")
        if entity_id:
            features[4] = min(entity_id / 10000.0, 1.0)

        if entity_type == "source":
            features[5] = 1.0
        else:
            features[6] = 1.0

        return features

    def _extract_interaction_features(self, event: dict[str, Any]) -> np.ndarray:
        """Extract edge features (interaction type).

        Args:
            event: Event data.

        Returns:
            16-dim edge feature vector.
        """
        features = np.zeros(self.edge_feature_dim, dtype=np.float32)

        event_type = event.get("type", "unknown")
        interaction_types = {
            "network_connection": 0,
            "process_creation": 1,
            "file_creation": 2,
            "file_read": 3,
            "file_write": 4,
            "file_delete": 5,
            "registry_read": 6,
            "registry_write": 7,
        }

        type_id = interaction_types.get(event_type, -1)
        if type_id >= 0:
            features[type_id] = 1.0

        return features
