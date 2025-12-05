"""
TIG Fabric Topology Generation
================================

Generates scale-free small-world network topologies that satisfy IIT requirements.
"""

from __future__ import annotations

import networkx as nx
import numpy as np

from .config import TopologyConfig


class TopologyGenerator:
    """
    Generates IIT-compliant network topologies.

    Implements Barabási-Albert scale-free model with triadic closure
    enhancements to achieve required clustering coefficients.
    """

    def __init__(self, config: TopologyConfig):
        self.config = config
        self.graph: nx.Graph | None = None

    def generate(self) -> nx.Graph:
        """
        Generate complete topology.

        Returns:
            NetworkX graph with IIT-compliant structure
        """
        # Step 1: Generate scale-free base
        self._generate_scale_free_base()

        # Step 2: Apply small-world rewiring if enabled
        if self.config.enable_small_world_rewiring:
            self._apply_small_world_rewiring()

        return self.graph

    def _generate_scale_free_base(self) -> None:
        """Generate scale-free network using Barabási-Albert preferential attachment."""
        # Start with a small complete graph
        m = self.config.min_degree
        self.graph = nx.barabasi_albert_graph(self.config.node_count, m, seed=42)

    def _apply_small_world_rewiring(self) -> None:
        """
        Apply triadic closure to increase clustering while maintaining small-world properties.

        ENHANCED VERSION (2025-10-07): More aggressive triadic closure to achieve
        target metrics: Clustering ≥0.70, ECI ≥0.85

        Instead of rewiring (which can reduce connectivity), we ADD edges to close
        triangles (triadic closure). This directly increases clustering coefficient.

        Algorithm:
        1. For each node, sample neighbor pairs aggressively
        2. Connect them with high probability (rewiring_probability)
        3. Multi-pass approach to reach target clustering

        Enhancement: Increased sampling rate and added second pass for stubborn cases.
        """
        # Set seed for reproducibility
        np.random.seed(42)

        if self.graph is None:
            return

        nodes = list(self.graph.nodes())

        # PASS 1: Conservative triadic closure
        for node in nodes:
            neighbors = list(self.graph.neighbors(node))

            if len(neighbors) < 2:
                continue

            # CONSERVATIVE: Moderate sampling - 3.5x degree or up to 35 samples
            # Balance between achieving targets and maintaining realistic density
            num_samples = min(int(len(neighbors) * 3.5), 35)

            for _ in range(num_samples):
                # Randomly pick 2 neighbors
                n1, n2 = np.random.choice(neighbors, size=2, replace=False)

                if not self.graph.has_edge(n1, n2):
                    # Add triangle-closing edge with probability
                    if np.random.random() < self.config.rewiring_probability:
                        self.graph.add_edge(n1, n2)

        # PASS 2: Targeted enhancement for high-degree nodes (hubs)
        # Hubs are critical for ECI - ensure they form moderately connected core
        # CONSERVATIVE: Reduced sampling to avoid over-densification
        #
        # NOTE: This pass only makes sense for larger graphs (16+ nodes) where
        # hub structure emerges. For small graphs (<12 nodes), hub enhancement
        # is skipped as all nodes have similar connectivity.
        if len(nodes) < 12:
            return

        degrees = dict(self.graph.degree())
        degree_values = list(degrees.values())

        # Safety: Skip hub enhancement if graph is degenerate (all same degree)
        if len(set(degree_values)) <= 2:
            return

        # Compute 75th percentile threshold - use sorted approach (NumPy-safe)
        sorted_degrees = sorted(degree_values)
        p75_index = int(len(sorted_degrees) * 0.75)
        threshold = (
            sorted_degrees[p75_index] if p75_index < len(sorted_degrees) else sorted_degrees[-1]
        )
        high_degree_nodes = [n for n, d in degrees.items() if d > threshold]

        for hub in high_degree_nodes:
            hub_neighbors = list(self.graph.neighbors(hub))

            if len(hub_neighbors) < 2:  # pragma: no cover - rare edge case in production
                continue

            # CONSERVATIVE: Reduced hub sampling - 1.5x degree or up to 15 samples
            num_hub_samples = min(int(len(hub_neighbors) * 1.5), 15)

            for _ in range(num_hub_samples):
                n1, n2 = np.random.choice(hub_neighbors, size=2, replace=False)

                if not self.graph.has_edge(n1, n2):
                    # Conservative probability for hub connections
                    if np.random.random() < 0.60:
                        self.graph.add_edge(n1, n2)
