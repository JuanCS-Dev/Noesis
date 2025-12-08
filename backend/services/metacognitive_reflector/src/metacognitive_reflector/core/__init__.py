"""
NOESIS Memory Fortress - Core Modules
======================================

Provides the complete Memory Fortress infrastructure:

Tiers:
- L1: Hot Cache (in-memory, <1ms)
- L2: Warm Storage (Redis, <10ms)
- L3: Cold Storage (Qdrant, <50ms)
- L4: Vault (JSON backup)

Components:
- Reflector: Main orchestrator
- MemoryClient: 4-tier memory storage
- SessionMemory: Conversation context management
- SelfReflector: Metacognitive learning loop
- PenalRegistry: Punishment persistence
- CriminalHistoryProvider: Recidivism tracking
- SoulTracker: Consciousness evolution
- HealthCheck: Comprehensive health monitoring
"""

from __future__ import annotations

from .memory import (
    MemoryClient, 
    MemoryEntry, 
    MemoryType, 
    SearchResult,
    SessionMemory,
    Turn,
    create_session,
    get_or_create_session,
)
from .resilience import (
    CircuitBreakerConfig,
    CircuitOpenError,
    L1HotCache,
    MemoryCircuitBreaker,
    VaultBackup,
    WriteAheadLog,
)
from .history import CriminalHistoryProvider, CriminalHistory, Conviction
from .soul_tracker import SoulTracker, SoulEventType, SoulPillar
from .health import (
    MemoryFortressHealthCheck,
    FortressHealth,
    TierHealth,
    HealthStatus,
    run_memory_fortress_health_check,
)
from .reflector import Reflector
from .self_reflection import (
    SelfReflector,
    ReflectionResult,
    ReflectionQuality,
    Insight,
    create_self_reflector,
)

__all__ = [
    # Main
    "Reflector",
    # Memory
    "MemoryClient",
    "MemoryEntry",
    "MemoryType",
    "SearchResult",
    # Session Memory
    "SessionMemory",
    "Turn",
    "create_session",
    "get_or_create_session",
    # Self-Reflection
    "SelfReflector",
    "ReflectionResult",
    "ReflectionQuality",
    "Insight",
    "create_self_reflector",
    # Resilience
    "MemoryCircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitOpenError",
    "L1HotCache",
    "VaultBackup",
    "WriteAheadLog",
    # Criminal History
    "CriminalHistoryProvider",
    "CriminalHistory",
    "Conviction",
    # Soul
    "SoulTracker",
    "SoulEventType",
    "SoulPillar",
    # Health
    "MemoryFortressHealthCheck",
    "FortressHealth",
    "TierHealth",
    "HealthStatus",
    "run_memory_fortress_health_check",
]
