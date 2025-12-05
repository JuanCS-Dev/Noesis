"""
TIG Fabric Metrics
==================

Consciousness-relevant metrics for TIG fabric validation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np


@dataclass
class FabricMetrics:
    """
    Consciousness-relevant metrics for TIG fabric validation.

    These metrics serve as Φ proxies - computable approximations of
    integrated information that validate structural compliance with IIT.
    """

    # Graph structure metrics
    node_count: int = 0
    edge_count: int = 0
    density: float = 0.0

    # IIT compliance metrics
    avg_clustering_coefficient: float = 0.0
    avg_path_length: float = 0.0
    algebraic_connectivity: float = 0.0  # Fiedler eigenvalue
    effective_connectivity_index: float = 0.0  # ECI - key Φ proxy

    # Non-degeneracy validation
    has_feed_forward_bottlenecks: bool = False
    bottleneck_locations: list[str] = field(default_factory=list)
    min_path_redundancy: int = 0  # Minimum alternative paths

    # Performance metrics
    avg_latency_us: float = 0.0
    max_latency_us: float = 0.0
    total_bandwidth_gbps: float = 0.0

    # Temporal
    last_update: float = field(default_factory=time.time)

    # Compatibility aliases for tests
    @property
    def eci(self) -> float:
        """Alias for effective_connectivity_index."""
        return self.effective_connectivity_index

    @property
    def clustering_coefficient(self) -> float:
        """Alias for avg_clustering_coefficient."""
        return self.avg_clustering_coefficient

    @property
    def connectivity_ratio(self) -> float:
        """Compute connectivity ratio (edges / max possible edges)."""
        if self.node_count < 2:
            return 0.0
        max_edges = self.node_count * (self.node_count - 1) / 2
        return self.edge_count / max_edges if max_edges > 0 else 0.0

    def validate_iit_compliance(self) -> tuple[bool, list[str]]:
        """
        Validate that fabric meets IIT structural requirements.

        Returns:
            (is_compliant, list_of_violations)
        """
        violations = []

        if self.effective_connectivity_index < 0.85:
            violations.append(f"ECI too low: {self.effective_connectivity_index:.3f} < 0.85")

        if self.avg_clustering_coefficient < 0.75:
            violations.append(f"Clustering too low: {self.avg_clustering_coefficient:.3f} < 0.75")

        if self.avg_path_length > np.log(self.node_count) * 2:
            violations.append(
                f"Path length too high: {self.avg_path_length:.2f} > {np.log(self.node_count) * 2:.2f}"
            )

        if self.algebraic_connectivity < 0.3:
            violations.append(
                f"Algebraic connectivity too low: {self.algebraic_connectivity:.3f} < 0.3"
            )

        if self.has_feed_forward_bottlenecks:
            violations.append(
                f"Feed-forward bottlenecks detected at: {', '.join(self.bottleneck_locations)}"
            )

        if self.min_path_redundancy < 3:
            violations.append(f"Insufficient path redundancy: {self.min_path_redundancy} < 3")

        return len(violations) == 0, violations
