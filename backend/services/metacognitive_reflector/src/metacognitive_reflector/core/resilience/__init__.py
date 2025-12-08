"""
NOESIS Memory Fortress - Resilience Patterns
=============================================

Circuit Breaker, WAL, and redundancy patterns for bulletproof memory.

Components:
- CircuitBreaker: Prevents cascading failures
- WriteAheadLog: Durability guarantee
- VaultBackup: Disaster recovery
- L1HotCache: Fast in-memory cache
"""

from __future__ import annotations

from .circuit_breaker import (
    CircuitBreakerConfig,
    CircuitOpenError,
    CircuitState,
    MemoryCircuitBreaker,
)
from .wal import WALEntry, WriteAheadLog
from .vault import VaultBackup, VaultChecksum
from .cache import L1HotCache

__all__ = [
    # Circuit Breaker
    "CircuitBreakerConfig",
    "CircuitOpenError",
    "CircuitState",
    "MemoryCircuitBreaker",
    # WAL
    "WALEntry",
    "WriteAheadLog",
    # Vault
    "VaultBackup",
    "VaultChecksum",
    # Cache
    "L1HotCache",
]

