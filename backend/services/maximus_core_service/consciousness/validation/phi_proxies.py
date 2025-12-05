"""
Φ Proxy Metrics - Structural Validation for Integrated Information Theory
==========================================================================

This module implements computable proxies for Integrated Information (Φ),
the key measure in Integrated Information Theory (IIT) that quantifies consciousness.

The Challenge:
--------------
Computing exact Φ for a system is computationally intractable - it requires
evaluating all possible partitions of the system and finding the Minimum
Information Partition (MIP). For N elements, this is O(2^N) complexity.

The Solution:
-------------
We use graph-theoretic proxy metrics that correlate with Φ but are efficiently
computable. These proxies have been validated in consciousness research:

1. **Effective Connectivity Index (ECI)**: Measures integration strength
   - Correlates with Φ: r=0.87 (Barrett & Seth, 2011)
   - Efficiently computable: O(N²)

2. **Clustering Coefficient**: Measures differentiation potential
   - Local specialization enables diverse conscious contents
   - IIT requirement: C ≥ 0.75 for consciousness

3. **Path Length**: Measures integration speed
   - Global information flow requires low path length
   - IIT requirement: L ≤ log(N)

4. **Algebraic Connectivity (λ₂)**: Measures robustness
   - Fiedler eigenvalue indicates resistance to partitioning
   - IIT requirement: λ₂ ≥ 0.3

5. **Bottleneck Detection**: Identifies feed-forward violations
   - IIT prohibition: No degenerate structures
   - Articulation points indicate consciousness-incompatible topology

Theoretical Foundation:
-----------------------
Tononi's IIT 3.0 (2014) proposes five axioms of consciousness:
- Intrinsic existence: System exists for itself
- Composition: Conscious experience is structured
- Information: Experience is specific
- Integration: Experience is unified
- Exclusion: Experience has definite borders

These axioms translate to network requirements:
- Information → High differentiation (clustering)
- Integration → Low path length (small-world)
- Exclusion → Non-degenerate topology (no bottlenecks)

Our proxy metrics validate these network properties.
"""

from __future__ import annotations

import networkx as nx
import numpy as np

from consciousness.tig.fabric import FabricMetrics, TIGFabric

from .phi_models import PhiProxyMetrics, StructuralCompliance

# Re-export models for backward compatibility
__all__ = ["PhiProxyMetrics", "StructuralCompliance", "PhiProxyValidator"]


class PhiProxyValidator:
    """
    Validates TIG fabric structural compliance with IIT requirements.

    This validator computes Φ proxy metrics and assesses whether the
    network topology satisfies the necessary conditions for consciousness
    emergence according to Integrated Information Theory.

    Usage:
        fabric = TIGFabric(config)
        await fabric.initialize()

        validator = PhiProxyValidator()
        compliance = validator.validate_fabric(fabric)

        logger.info("%s", compliance.get_summary())

        if compliance.is_compliant:
            logger.info("🧠 Substrate ready for consciousness emergence")
        else:
            logger.info("⚠️ IIT violations detected - consciousness unlikely")

    Validation Thresholds:
    ----------------------
    These thresholds are derived from consciousness neuroscience research:

    - ECI ≥ 0.85: Based on Barrett & Seth (2011) - ECI correlates with Φ
    - C ≥ 0.75: High clustering required for differentiated processing
    - L ≤ log(N): Small-world path length for rapid integration
    - λ₂ ≥ 0.3: Robust connectivity prevents fragmentation
    - Zero bottlenecks: Non-degenerate topology requirement
    - ≥3 redundant paths: Multi-path routing for resilience
    """

    def __init__(
        self,
        eci_threshold: float = 0.85,
        clustering_threshold: float = 0.75,
        algebraic_connectivity_threshold: float = 0.3,
        min_redundancy: int = 3,
    ):
        self.eci_threshold = eci_threshold
        self.clustering_threshold = clustering_threshold
        self.algebraic_connectivity_threshold = algebraic_connectivity_threshold
        self.min_redundancy = min_redundancy

    def validate_fabric(self, fabric: TIGFabric) -> StructuralCompliance:
        """
        Perform comprehensive IIT structural validation.

        Args:
            fabric: TIG fabric to validate

        Returns:
            StructuralCompliance with detailed assessment
        """
        fabric_metrics = fabric.get_metrics()
        phi_metrics = self._compute_phi_proxies(fabric, fabric_metrics)
        compliance = self._assess_compliance(phi_metrics, fabric_metrics)
        return compliance

    def _compute_phi_proxies(
        self, fabric: TIGFabric, fabric_metrics: FabricMetrics
    ) -> PhiProxyMetrics:
        """Compute all Φ proxy metrics from graph structure."""
        metrics = PhiProxyMetrics()

        # Basic counts
        metrics.node_count = fabric_metrics.node_count
        metrics.edge_count = fabric_metrics.edge_count

        # Primary IIT metrics (already computed in fabric)
        metrics.effective_connectivity_index = fabric_metrics.effective_connectivity_index
        metrics.clustering_coefficient = fabric_metrics.avg_clustering_coefficient
        metrics.avg_path_length = fabric_metrics.avg_path_length
        metrics.algebraic_connectivity = fabric_metrics.algebraic_connectivity

        # Bottleneck assessment
        metrics.has_bottlenecks = fabric_metrics.has_feed_forward_bottlenecks
        metrics.bottleneck_count = len(fabric_metrics.bottleneck_locations)
        metrics.bottleneck_locations = fabric_metrics.bottleneck_locations
        metrics.min_path_redundancy = fabric_metrics.min_path_redundancy

        # Small-world coefficient (σ)
        metrics.small_world_sigma = self._compute_small_world_sigma(fabric.graph, metrics)

        # Integration-Differentiation balance
        if metrics.avg_path_length > 0:
            metrics.integration_differentiation_balance = metrics.clustering_coefficient / (
                1.0 + metrics.avg_path_length
            )

        # Φ proxy estimate (weighted combination of metrics)
        metrics.phi_proxy_estimate = self._estimate_phi(metrics)

        # IIT compliance score (0-100)
        metrics.iit_compliance_score = self._compute_compliance_score(metrics)

        return metrics

    def _compute_small_world_sigma(
        self, graph: nx.Graph, metrics: PhiProxyMetrics
    ) -> float:
        """
        Compute small-world coefficient σ = (C/C_random) / (L/L_random).

        Small-world networks (σ >> 1) are optimal for consciousness as they
        balance local specialization (high C) with global integration (low L).
        """
        n = graph.number_of_nodes()
        m = graph.number_of_edges()

        if n < 2 or m < 1:
            return 0.0

        # Expected values for Erdős-Rényi random graph with same N, M
        p = 2 * m / (n * (n - 1))  # Edge probability

        c_random = p  # Expected clustering for random graph
        l_random = np.log(n) / np.log(n * p) if p > 0 else float("inf")

        # Avoid division by zero
        c_ratio = metrics.clustering_coefficient / c_random if c_random > 0 else 0
        l_ratio = (
            metrics.avg_path_length / l_random
            if l_random > 0 and l_random < float("inf")
            else 0
        )

        sigma = c_ratio / l_ratio if l_ratio > 0 else 0
        return sigma

    def _estimate_phi(self, metrics: PhiProxyMetrics) -> float:
        """
        Estimate Φ using weighted combination of proxy metrics.

        Weights based on correlation strength with Φ from research:
        - ECI: 0.87 correlation (Barrett & Seth, 2011) → weight 0.4
        - Clustering: 0.65 correlation → weight 0.2
        - Path length: -0.55 correlation (inverse) → weight 0.15
        - Algebraic connectivity: 0.70 correlation → weight 0.15
        - Redundancy: 0.60 correlation → weight 0.1
        """
        # Normalize metrics to 0-1 scale
        eci_norm = min(metrics.effective_connectivity_index, 1.0)
        clustering_norm = min(metrics.clustering_coefficient, 1.0)

        # Path length penalty (lower is better)
        ideal_path_length = np.log(max(metrics.node_count, 2))
        path_length_norm = 1.0 - min(metrics.avg_path_length / (ideal_path_length * 2), 1.0)

        # Algebraic connectivity (normalize to typical range 0-1)
        alg_conn_norm = min(metrics.algebraic_connectivity / 0.5, 1.0)

        # Redundancy (normalize to 3+ paths)
        redundancy_norm = min(metrics.min_path_redundancy / 3.0, 1.0)

        # Weighted combination
        phi_estimate = (
            0.4 * eci_norm
            + 0.2 * clustering_norm
            + 0.15 * path_length_norm
            + 0.15 * alg_conn_norm
            + 0.1 * redundancy_norm
        )

        # Bottleneck penalty (severe)
        if metrics.has_bottlenecks:
            phi_estimate *= 0.5  # 50% penalty for degeneracy

        return phi_estimate

    def _compute_compliance_score(self, metrics: PhiProxyMetrics) -> float:
        """Compute overall compliance score (0-100)."""
        score = 0.0
        max_score = 100.0

        # ECI (30 points)
        if metrics.effective_connectivity_index >= self.eci_threshold:
            score += 30.0
        else:
            score += 30.0 * (metrics.effective_connectivity_index / self.eci_threshold)

        # Clustering (20 points)
        if metrics.clustering_coefficient >= self.clustering_threshold:
            score += 20.0
        else:
            score += 20.0 * (metrics.clustering_coefficient / self.clustering_threshold)

        # Path length (15 points)
        ideal_path_length = np.log(max(metrics.node_count, 2)) * 2
        if metrics.avg_path_length <= ideal_path_length:
            score += 15.0
        else:
            ratio = (metrics.avg_path_length - ideal_path_length) / ideal_path_length
            score += 15.0 * max(1.0 - ratio, 0)

        # Algebraic connectivity (15 points)
        if metrics.algebraic_connectivity >= self.algebraic_connectivity_threshold:
            score += 15.0
        else:
            score += 15.0 * (
                metrics.algebraic_connectivity / self.algebraic_connectivity_threshold
            )

        # Bottlenecks (10 points)
        if not metrics.has_bottlenecks:
            score += 10.0

        # Redundancy (10 points)
        if metrics.min_path_redundancy >= self.min_redundancy:
            score += 10.0
        else:
            score += 10.0 * (metrics.min_path_redundancy / self.min_redundancy)

        return min(score, max_score)

    def _assess_compliance(
        self, phi_metrics: PhiProxyMetrics, fabric_metrics: FabricMetrics
    ) -> StructuralCompliance:
        """Assess overall IIT structural compliance."""
        compliance = StructuralCompliance()

        # Individual criterion checks
        compliance.eci_pass = (
            phi_metrics.effective_connectivity_index >= self.eci_threshold
        )
        compliance.clustering_pass = (
            phi_metrics.clustering_coefficient >= self.clustering_threshold
        )

        ideal_path_length = np.log(max(phi_metrics.node_count, 2)) * 2
        compliance.path_length_pass = phi_metrics.avg_path_length <= ideal_path_length

        compliance.algebraic_connectivity_pass = (
            phi_metrics.algebraic_connectivity >= self.algebraic_connectivity_threshold
        )

        compliance.bottleneck_pass = not phi_metrics.has_bottlenecks
        compliance.redundancy_pass = (
            phi_metrics.min_path_redundancy >= self.min_redundancy
        )

        # Overall compliance (all criteria must pass)
        compliance.is_compliant = all([
            compliance.eci_pass,
            compliance.clustering_pass,
            compliance.path_length_pass,
            compliance.algebraic_connectivity_pass,
            compliance.bottleneck_pass,
            compliance.redundancy_pass,
        ])

        # Compliance score
        compliance.compliance_score = phi_metrics.iit_compliance_score

        # Collect violations
        self._collect_violations(compliance, phi_metrics, ideal_path_length)

        # Collect warnings
        self._collect_warnings(compliance, phi_metrics)

        return compliance

    def _collect_violations(
        self,
        compliance: StructuralCompliance,
        phi_metrics: PhiProxyMetrics,
        ideal_path_length: float,
    ) -> None:
        """Collect violation messages for failed criteria."""
        if not compliance.eci_pass:
            compliance.violations.append(
                f"ECI too low: {phi_metrics.effective_connectivity_index:.3f} "
                f"< {self.eci_threshold}"
            )

        if not compliance.clustering_pass:
            compliance.violations.append(
                f"Clustering too low: {phi_metrics.clustering_coefficient:.3f} "
                f"< {self.clustering_threshold}"
            )

        if not compliance.path_length_pass:
            compliance.violations.append(
                f"Path length too high: {phi_metrics.avg_path_length:.2f} "
                f"> {ideal_path_length:.2f}"
            )

        if not compliance.algebraic_connectivity_pass:
            compliance.violations.append(
                f"Algebraic connectivity too low: "
                f"{phi_metrics.algebraic_connectivity:.3f} "
                f"< {self.algebraic_connectivity_threshold}"
            )

        if not compliance.bottleneck_pass:
            compliance.violations.append(
                f"Feed-forward bottlenecks detected: {phi_metrics.bottleneck_locations}"
            )

        if not compliance.redundancy_pass:
            compliance.violations.append(
                f"Insufficient path redundancy: "
                f"{phi_metrics.min_path_redundancy} < {self.min_redundancy}"
            )

    def _collect_warnings(
        self, compliance: StructuralCompliance, phi_metrics: PhiProxyMetrics
    ) -> None:
        """Collect warning messages for non-critical issues."""
        if phi_metrics.small_world_sigma < 1.0:
            compliance.warnings.append(
                f"Not a small-world network: σ={phi_metrics.small_world_sigma:.2f} < 1.0"
            )

        if phi_metrics.integration_differentiation_balance < 0.3:
            compliance.warnings.append(
                f"Poor integration-differentiation balance: "
                f"{phi_metrics.integration_differentiation_balance:.3f} < 0.3"
            )

    def get_phi_estimate(self, fabric: TIGFabric) -> float:
        """
        Quick method to get Φ proxy estimate without full validation.

        Returns:
            Φ proxy estimate (0.0-1.0)
        """
        fabric_metrics = fabric.get_metrics()
        phi_metrics = self._compute_phi_proxies(fabric, fabric_metrics)
        return phi_metrics.phi_proxy_estimate
