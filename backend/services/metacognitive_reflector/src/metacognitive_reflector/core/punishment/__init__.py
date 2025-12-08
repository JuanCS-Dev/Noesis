"""
MAXIMUS 2.0 - Punishment Protocol
=================================

Execution and persistence of punishments:
- PenalRegistry: Redis + MIRIX persistence
- PunishmentHandlers: Execute real punishment actions
- Quarantine: Agent isolation
- ReEducation: Learning loops
- Rollback: Action reversal
"""

from __future__ import annotations


from .models import (
    OffenseType,
    PenalRecord,
    PenalStatus,
    WriteStrategy,
)
from .penal_registry import (
    PenalRegistry,
    check_agent_punishment,
)
from .storage_backends import (
    InMemoryBackend,
    RedisBackend,
    StorageBackend,
)
from .base_handler import (
    PunishmentHandler,
    PunishmentOutcome,
    PunishmentResult,
)
from .handlers import (
    DeletionHandler,
    QuarantineHandler,
    ReEducationHandler,
    RollbackHandler,
)
from .executor import PunishmentExecutor

__all__ = [
    # Models
    "OffenseType",
    "PenalRecord",
    "PenalStatus",
    "WriteStrategy",
    # Registry
    "PenalRegistry",
    "check_agent_punishment",
    # Backends
    "InMemoryBackend",
    "RedisBackend",
    "StorageBackend",
    # Handlers
    "DeletionHandler",
    "PunishmentHandler",
    "PunishmentOutcome",
    "PunishmentResult",
    "QuarantineHandler",
    "ReEducationHandler",
    "RollbackHandler",
    # Executor
    "PunishmentExecutor",
]
