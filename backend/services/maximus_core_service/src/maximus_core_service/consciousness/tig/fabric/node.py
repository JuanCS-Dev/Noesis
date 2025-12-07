"""
TIG Node - Individual processing unit implementation
=====================================================

This module implements the TIGNode class - individual processing units
within the TIG fabric.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .models import NodeState, ProcessingState, TIGConnection

if TYPE_CHECKING:
    from .core import TIGFabric


@dataclass
class TIGNode:
    """
    A processing unit within the TIG fabric.

    Each node represents a Specialized Processing Module (SPM) that can:
    - Process domain-specific information independently (differentiation)
    - Participate in global synchronization events (integration)
    - Maintain recurrent connections to other nodes (non-degeneracy)

    Biological Analogy:
    -------------------
    TIG nodes are analogous to cortical columns in the brain - specialized
    processors that maintain local function while participating in global
    conscious states through transient synchronization.
    """

    id: str
    connections: dict[str, TIGConnection] = field(default_factory=dict)
    state: ProcessingState = field(default_factory=ProcessingState)
    node_state: NodeState = NodeState.INITIALIZING
    message_queue: asyncio.Queue = field(default_factory=lambda: asyncio.Queue(maxsize=10000))

    # Performance metrics
    messages_processed: int = 0
    last_heartbeat: float = field(default_factory=time.time)

    @property
    def neighbors(self) -> list[str]:
        """Return list of active neighbor node IDs (compatibility property)."""
        return [node_id for node_id, conn in self.connections.items() if conn.active]

    def get_degree(self) -> int:
        """Number of active connections (node degree in graph theory)."""
        return sum(1 for conn in self.connections.values() if conn.active)

    def get_clustering_coefficient(self, fabric: TIGFabric) -> float:
        """
        Compute local clustering coefficient for this node.

        Clustering coefficient measures how well a node's neighbors are
        connected to each other - critical for differentiated processing.

        C_i = (# triangles involving node i) / (# possible triangles)
        """
        neighbors = set(conn.remote_node_id for conn in self.connections.values() if conn.active)

        if len(neighbors) < 2:
            return 0.0

        # Count triangles: neighbor pairs that are also connected
        triangles = 0
        possible = len(neighbors) * (len(neighbors) - 1) / 2

        for n1 in neighbors:
            for n2 in neighbors:
                if n1 < n2:  # Avoid double counting
                    node_n1 = fabric.nodes.get(n1)
                    if node_n1 and n2 in node_n1.connections and node_n1.connections[n2].active:
                        triangles += 1

        return triangles / possible if possible > 0 else 0.0

    async def broadcast_to_neighbors(self, message: dict[str, Any], priority: int = 0) -> int:
        """
        Broadcast message to all connected neighbors.

        This implements the reentrant signaling critical for GWD ignition.
        During ESGT events, high-priority broadcasts create transient
        coherent states across the fabric.

        Args:
            message: Content to broadcast
            priority: Higher priority messages preempt lower priority

        Returns:
            Number of neighbors successfully reached
        """
        successful = 0
        tasks = []

        for conn in self.connections.values():
            if conn.active and conn.weight > 0.1:  # Only use quality connections
                tasks.append(self._send_to_neighbor(conn.remote_node_id, message, priority))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            successful = sum(1 for r in results if r is True)

        return successful

    async def _send_to_neighbor(
        self, neighbor_id: str, message: dict[str, Any], priority: int
    ) -> bool:
        """Internal method to send message to specific neighbor."""
        # In production, this would use actual network protocols
        # For now, we simulate with direct queue insertion
        try:
            # Simulate network latency
            conn = self.connections.get(neighbor_id)
            if conn:
                await asyncio.sleep(conn.latency_us / 1_000_000)  # Convert to seconds

            # In real implementation, would send via network
            # Here we just log success
            return True
        except Exception:
            return False
