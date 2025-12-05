"""
Módulo Florescimento: Auto-Percepção Consciente e Introspecção.
"""

from .unified_self import UnifiedSelfConcept, ComputationalState, EpisodicMemorySnapshot
from .consciousness_bridge import ConsciousnessBridge, IntrospectiveResponse
from .mirror_test import MirrorTestValidator, MirrorTestResult
from .introspection_api import router as florescimento_router, initialize_florescimento

__all__ = [
    "UnifiedSelfConcept",
    "ComputationalState",
    "EpisodicMemorySnapshot",
    "ConsciousnessBridge",
    "IntrospectiveResponse",
    "MirrorTestValidator",
    "MirrorTestResult",
    "florescimento_router",
    "initialize_florescimento",
]