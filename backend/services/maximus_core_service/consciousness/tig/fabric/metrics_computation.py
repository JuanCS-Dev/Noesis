"""
TIG Fabric Metrics Computation Mixin.

Provides metrics computation methods for TIGFabric.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import networkx as nx
import numpy as np

if TYPE_CHECKING:
    from .core import TIGFabric


class MetricsComputationMixin:
    """Mixin providing metrics computation methods for TIGFabric.

    Methods:
        _compute_metrics: Compute all consciousness-relevant metrics.
        _compute_eci: Compute Effective Connectivity Index.
        _detect_bottlenecks: Detect feed-forward bottlenecks.
    """

    def _compute_metrics(self: TIGFabric) -> None:
        """Compute all consciousness-relevant metrics."""
        # Basic graph metrics
        self.metrics.node_count = self.graph.number_of_nodes()
        self.metrics.edge_count = self.graph.number_of_edges()
        self.metrics.density = nx.density(self.graph)

        # IIT compliance metrics
        self.metrics.avg_clustering_coefficient = nx.average_clustering(self.graph)

        # Average path length (only for connected components)
        if nx.is_connected(self.graph):
            self.metrics.avg_path_length = nx.average_shortest_path_length(self.graph)
        else:
            # Use largest connected component
            largest_cc = max(nx.connected_components(self.graph), key=len)
            subgraph = self.graph.subgraph(largest_cc)
            self.metrics.avg_path_length = nx.average_shortest_path_length(subgraph)

        # Algebraic connectivity (Fiedler eigenvalue) - REMOVED for performance
        # The exact calculation is O(n³) and causes hangs for graphs >16 nodes
        # Use fast approximation: connectivity ≈ min_degree / n
        # This captures the "weakest link" in the graph
        if self.graph.number_of_nodes() > 0:
            degrees = dict(self.graph.degree())
            min_degree = min(degrees.values()) if degrees else 0
            # Normalize by number of nodes for scale-free comparison
            self.metrics.algebraic_connectivity = min_degree / self.graph.number_of_nodes()
        else:  # pragma: no cover - unreachable
            self.metrics.algebraic_connectivity = 0.0

        # Effective Connectivity Index (ECI) - key Φ proxy
        self.metrics.effective_connectivity_index = self._compute_eci()

        # Feed-forward bottleneck detection
        self._detect_bottlenecks()

        # Performance metrics
        latencies = [
            conn.latency_us for node in self.nodes.values() for conn in node.connections.values()
        ]
        self.metrics.avg_latency_us = np.mean(latencies) if latencies else 0.0
        self.metrics.max_latency_us = np.max(latencies) if latencies else 0.0

        bandwidths = [
            conn.bandwidth_bps / 1e9
            for node in self.nodes.values()
            for conn in node.connections.values()
        ]
        self.metrics.total_bandwidth_gbps = np.sum(bandwidths) if bandwidths else 0.0

    def _compute_eci(self: TIGFabric) -> float:
        """Compute Effective Connectivity Index - a key Φ proxy.

        ECI measures information flow efficiency through the network.
        Uses networkx's global_efficiency which computes:

        E = (1/(n*(n-1))) * Σ(1/d(i,j))

        where d(i,j) is shortest path length between nodes i and j.

        This metric captures:
        - Short average path length (small-world property)
        - Multiple redundant paths (high connectivity)
        - Absence of bottlenecks (non-degeneracy)

        Time complexity: O(n^2) using Dijkstra's algorithm.

        For IIT compliance, we need ECI ≥ 0.85:
        - Complete graph: E = 1.0
        - Small-world topology: E ≈ 0.85-0.95
        - Random graph: E ≈ 0.60-0.70

        Returns:
            Float value in [0, 1] range representing connectivity efficiency.
        """
        if self.metrics.node_count < 2:
            return 0.0

        # Use networkx's efficient global efficiency computation
        # This is O(n^2) vs exponential for path enumeration
        efficiency = nx.global_efficiency(self.graph)

        # Global efficiency is already in [0, 1] range
        return min(efficiency, 1.0)

    def _detect_bottlenecks(self: TIGFabric) -> None:
        """Detect feed-forward bottlenecks that would prevent consciousness.

        A bottleneck exists when removing a node partitions the graph,
        indicating feed-forward information flow (IIT violation).
        """
        articulation_points = list(nx.articulation_points(self.graph))

        if articulation_points:
            self.metrics.has_feed_forward_bottlenecks = True
            self.metrics.bottleneck_locations = [f"tig-node-{ap:03d}" for ap in articulation_points]
        else:
            self.metrics.has_feed_forward_bottlenecks = False
            self.metrics.bottleneck_locations = []

        # Compute minimum path redundancy
        if self.metrics.node_count > 1:
            redundancies = []
            node_list = list(self.nodes.keys())

            # Sample first 10 for efficiency
            for i, node_a_id in enumerate(node_list[:10]):
                for node_b_id in node_list[i + 1 : i + 11]:
                    try:
                        paths = list(
                            nx.all_simple_paths(
                                self.graph,
                                source=int(node_a_id.split("-")[-1]),
                                target=int(node_b_id.split("-")[-1]),
                                cutoff=4,
                            )
                        )
                        redundancies.append(len(paths))
                    except nx.NetworkXNoPath:  # pragma: no cover
                        redundancies.append(0)

            self.metrics.min_path_redundancy = min(redundancies) if redundancies else 0
