"""
TIG Fabric Configuration
=========================

Configuration classes for TIG fabric topology generation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TopologyConfig:
    """
    Configuration for generating TIG fabric topology.

    These parameters are carefully tuned to satisfy IIT requirements:
    - node_count: System size (larger = more differentiation potential)
    - density: Connection density (higher = more integration)
    - gamma: Scale-free exponent (2.5 = optimal hub/spoke balance)
    - clustering_target: Target clustering coefficient (0.75 = high differentiation)

    Parameter Tuning History:
    - 2025-10-06: min_degree 3→5, rewiring_probability 0.1→0.35, target_density 0.15→0.20
    - 2025-10-07 (PAGANI FIX v1): Over-aggressive - density 99.2% (complete graph!)
    - 2025-10-07 (PAGANI FIX v2): Still too aggressive - density 100%
    - 2025-10-07 (PAGANI FIX v3 - CONSERVATIVE): Target realistic density
      * rewiring_probability: 0.72→0.58 (more conservative closure)
      * min_degree: 5→5 (maintained)
      * Reduced sampling rates: Pass1 6x→3.5x, Pass2 2.5x→1.5x
      * Hub probability: 0.75→0.60
      * Target: C≥0.75, ECI≥0.85, Density ~30-40% (realistic network)
    """

    node_count: int = 16
    min_degree: int = 5  # Balanced base connectivity
    target_density: float = 0.20  # 20% connectivity for better integration
    gamma: float = 2.5  # Scale-free power law exponent
    clustering_target: float = 0.75
    enable_small_world_rewiring: bool = True
    rewiring_probability: float = 0.58  # CONSERVATIVE: Realistic density with IIT targets

    def __init__(
        self,
        node_count: int = 16,
        num_nodes: int | None = None,  # Alias for compatibility
        min_degree: int = 5,
        avg_degree: int | None = None,  # Alias for min_degree
        target_density: float = 0.20,
        gamma: float = 2.5,
        clustering_target: float = 0.75,
        enable_small_world_rewiring: bool = True,
        rewiring_probability: float = 0.58,
        rewire_probability: float | None = None,
    ):  # Alias for rewiring_probability
        # Support both node_count and num_nodes (alias)
        if num_nodes is not None:
            node_count = num_nodes

        # Support both min_degree and avg_degree (alias)
        if avg_degree is not None:
            min_degree = avg_degree

        # Support both rewiring_probability and rewire_probability (alias)
        if rewire_probability is not None:
            rewiring_probability = rewire_probability

        self.node_count = node_count
        self.min_degree = min_degree
        self.target_density = target_density
        self.gamma = gamma
        self.clustering_target = clustering_target
        self.enable_small_world_rewiring = enable_small_world_rewiring
        self.rewiring_probability = rewiring_probability
