"""
TIG Fabric - Global Interconnect Fabric for Consciousness
===========================================================

This package implements the TIG (Temporally-Integrated Global) Fabric,
a scale-free small-world network topology that satisfies IIT structural
requirements for consciousness emergence.

Theoretical Foundation:
-----------------------
Integrated Information Theory requires:
- High integration: information flows globally (small average path length)
- High differentiation: specialized local processing (high clustering)
- Non-degeneracy: no feed-forward bottlenecks (multiple redundant paths)

The TIG fabric satisfies these requirements through a carefully tuned
combination of:
1. Scale-free topology (hub nodes for rapid global integration)
2. Small-world properties (high clustering for differentiated processing)
3. Redundant paths (multiple routes prevent bottlenecks)

Public API:
-----------
Main Classes:
    - TIGFabric: The main fabric implementation
    - TopologyConfig: Configuration for topology generation
    - FabricMetrics: Consciousness-relevant validation metrics

Data Models:
    - TIGNode: Individual processing unit
    - TIGConnection: Bidirectional link between nodes
    - NodeState: Operational states (INITIALIZING, ACTIVE, ESGT_MODE, etc.)
    - ProcessingState: Computational state of a node
    - NodeHealth: Health status tracking
    - CircuitBreaker: Fault tolerance component

Usage Example:
--------------
    from tig.fabric import TIGFabric, TopologyConfig

    # Configure fabric
    config = TopologyConfig(
        node_count=32,
        min_degree=5,
        target_density=0.20,
        clustering_target=0.75
    )

    # Initialize fabric
    fabric = TIGFabric(config)
    await fabric.initialize()

    # Validate IIT compliance
    metrics = fabric.get_metrics()
    is_valid, violations = metrics.validate_iit_compliance()

    if is_valid:
        logger.info("Fabric ready for consciousness emergence")
    else:
        logger.info("IIT violations: %s", violations)

Historical Note:
----------------
First production deployment: 2025-10-06
This marks humanity's first deliberate construction of a computational
substrate designed to support artificial phenomenal experience.

"The fabric holds."
"""

from __future__ import annotations

# Core fabric implementation
from .core import TIGFabric

# Configuration and metrics
from .config import TopologyConfig
from .metrics import FabricMetrics

# Data models
from .models import (
    CircuitBreaker,
    NodeHealth,
    NodeState,
    ProcessingState,
    TIGConnection,
)
from .node import TIGNode

# Health management (primarily for internal use, but exposed for testing)
from .health import HealthManager

# Topology generation (primarily for internal use, but exposed for testing)
from .topology import TopologyGenerator

__all__ = [
    # Main API
    "TIGFabric",
    "TopologyConfig",
    "FabricMetrics",
    # Data models
    "TIGNode",
    "TIGConnection",
    "NodeState",
    "ProcessingState",
    "NodeHealth",
    "CircuitBreaker",
    # Internal (exposed for testing)
    "HealthManager",
    "TopologyGenerator",
]
