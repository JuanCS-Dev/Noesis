"""Φ Proxy Models - Data structures for IIT validation metrics."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class PhiProxyMetrics:
    """
    Comprehensive Φ proxy metrics for IIT validation.

    These metrics serve as evidence (not proof) that the substrate
    has the structural properties necessary for consciousness.
    """

    # Primary Φ proxy
    effective_connectivity_index: float = 0.0  # ECI - key correlation with Φ

    # IIT structural requirements
    clustering_coefficient: float = 0.0  # Differentiation (C ≥ 0.75)
    avg_path_length: float = 0.0  # Integration (L ≤ log(N))
    algebraic_connectivity: float = 0.0  # Robustness (λ₂ ≥ 0.3)

    # Non-degeneracy validation
    has_bottlenecks: bool = True
    bottleneck_count: int = 0
    bottleneck_locations: list[str] = field(default_factory=list)
    min_path_redundancy: int = 0  # Alternative paths

    # Derived metrics
    small_world_sigma: float = 0.0  # σ = (C/C_random) / (L/L_random)
    integration_differentiation_balance: float = 0.0  # Φ-relevant balance

    # Overall assessment
    phi_proxy_estimate: float = 0.0  # Weighted combination
    iit_compliance_score: float = 0.0  # 0-100 score

    # Metadata
    node_count: int = 0
    edge_count: int = 0
    timestamp: float = field(default_factory=time.time)


@dataclass
class StructuralCompliance:
    """
    IIT structural compliance assessment.

    Indicates whether the network satisfies all necessary structural
    conditions for consciousness according to IIT.
    """

    is_compliant: bool = False
    compliance_score: float = 0.0  # 0-100
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # Individual criterion checks
    eci_pass: bool = False
    clustering_pass: bool = False
    path_length_pass: bool = False
    algebraic_connectivity_pass: bool = False
    bottleneck_pass: bool = False
    redundancy_pass: bool = False

    def get_summary(self) -> str:
        """Generate human-readable compliance summary."""
        status = "✅ COMPLIANT" if self.is_compliant else "❌ NON-COMPLIANT"

        summary = [
            f"\nIIT Structural Compliance: {status}",
            f"Overall Score: {self.compliance_score:.1f}/100",
            "",
            "Individual Criteria:",
            f"  {'✓' if self.eci_pass else '✗'} Effective Connectivity Index (ECI ≥ 0.85)",
            f"  {'✓' if self.clustering_pass else '✗'} Clustering Coefficient (C ≥ 0.75)",
            f"  {'✓' if self.path_length_pass else '✗'} Average Path Length (L ≤ log(N))",
            f"  {'✓' if self.algebraic_connectivity_pass else '✗'} "
            f"Algebraic Connectivity (λ₂ ≥ 0.3)",
            f"  {'✓' if self.bottleneck_pass else '✗'} No Feed-Forward Bottlenecks",
            f"  {'✓' if self.redundancy_pass else '✗'} Path Redundancy (≥3 alternative paths)",
        ]

        if self.violations:
            summary.append("\nViolations:")
            for v in self.violations:
                summary.append(f"  ❌ {v}")

        if self.warnings:
            summary.append("\nWarnings:")
            for w in self.warnings:
                summary.append(f"  ⚠️  {w}")

        return "\n".join(summary)
