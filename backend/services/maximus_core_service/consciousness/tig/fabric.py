"""
TIG Fabric - Backward Compatibility Module
===========================================

This module maintains backward compatibility by re-exporting all public
classes from the refactored fabric/ subdirectory.

DEPRECATED: This file exists only for backward compatibility.
New code should import directly from tig.fabric submodules:

    from tig.fabric import TIGFabric, TopologyConfig, FabricMetrics

The original 1263-line implementation has been refactored into a logical
subdirectory structure with modules under 500 lines each:

    fabric/
    ├── __init__.py        (111 lines) - Public API exports
    ├── config.py          (73 lines)  - Configuration classes
    ├── core.py            (488 lines) - Main TIGFabric implementation
    ├── health.py          (317 lines) - Health monitoring & fault tolerance
    ├── metrics.py         (95 lines)  - IIT validation metrics
    ├── models.py          (165 lines) - Data classes and enums
    ├── node.py            (127 lines) - TIGNode implementation
    └── topology.py        (130 lines) - Topology generation

Historical Note:
----------------
Original file: 1263 lines (2025-12-02)
Refactored: 8 modules, largest 488 lines
Refactoring date: 2025-12-02

"Clarity Over Cleverness" - MAXIMUS Code Constitution
"""

from __future__ import annotations

# Re-export all public classes for backward compatibility
from .fabric import (
    CircuitBreaker,
    FabricMetrics,
    HealthManager,
    NodeHealth,
    NodeState,
    ProcessingState,
    TIGConnection,
    TIGFabric,
    TIGNode,
    TopologyConfig,
    TopologyGenerator,
)

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
