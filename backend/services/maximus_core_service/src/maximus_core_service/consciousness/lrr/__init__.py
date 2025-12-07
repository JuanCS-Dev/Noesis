"""
LRR - Loop de Raciocínio Recursivo
==================================

Metacognition engine for MAXIMUS consciousness system.

Este módulo implementa raciocínio recursivo de ordem superior,
permitindo que MAXIMUS pense sobre seu próprio pensamento.

Components:
-----------
- RecursiveReasoner: Motor de raciocínio recursivo
- ContradictionDetector: Detecção de inconsistências lógicas
- MetaMonitor: Monitoramento metacognitivo
- IntrospectionEngine: Geração de relatórios em primeira pessoa

Baseline Científico:
-------------------
- Carruthers (2009): Higher-Order Thoughts
- Hofstadter (1979): Strange Loops
- Fleming & Lau (2014): Metacognitive sensitivity

Authors: Claude Code + Juan
Version: 1.0.0
Date: 2025-12-02
Status: DOUTRINA VÉRTICE v2.0 COMPLIANT
"""

from __future__ import annotations


# Belief Models
from .belief_models import (
    Belief,
    BeliefType,
    ContradictionType,
    ResolutionStrategy,
)

# Contradiction Models
from .contradiction_models import (
    Contradiction,
    Resolution,
)

# Reasoning Models
from .reasoning_models import (
    ReasoningLevel,
    ReasoningStep,
    RecursiveReasoningResult,
)

# Belief Graph
from .belief_graph import BeliefGraph

# Contradiction Detection & Revision
from .contradiction_detector import (
    BeliefRevision,
    ContradictionDetector,
    RevisionOutcome,
)

# Meta-Monitoring
from .meta_monitor import MetaMonitor, MetaMonitoringReport

# Introspection
from .introspection_engine import IntrospectionEngine, IntrospectionReport

# Recursive Reasoner
from .recursive_reasoner import RecursiveReasoner

__all__ = [
    # Core reasoning
    "RecursiveReasoner",
    "RecursiveReasoningResult",
    "ReasoningLevel",
    "ReasoningStep",
    # Belief management
    "Belief",
    "BeliefGraph",
    "Contradiction",
    "Resolution",
    "BeliefType",
    "ContradictionType",
    "ResolutionStrategy",
    # Advanced modules
    "ContradictionDetector",
    "BeliefRevision",
    "RevisionOutcome",
    "MetaMonitor",
    "MetaMonitoringReport",
    "IntrospectionEngine",
    "IntrospectionReport",
]

__version__ = "1.0.0"
