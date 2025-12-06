"""
Kill Switch Models.

Enums and dataclasses for kill switch operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional


class ShutdownLevel(Enum):
    """Shutdown urgency levels."""

    GRACEFUL = "graceful"  # Controlled shutdown with cleanup
    IMMEDIATE = "immediate"  # Fast shutdown, minimal cleanup
    EMERGENCY = "emergency"  # Instant kill, no cleanup
    NUCLEAR = "nuclear"  # Destroy everything including data


class ComponentType(Enum):
    """Types of components that can be killed."""

    CONTAINER = "container"
    PROCESS = "process"
    NETWORK = "network"
    VM = "vm"
    SERVICE = "service"


@dataclass
class KillTarget:
    """Target for kill switch activation."""

    id: str
    name: str
    component_type: ComponentType
    layer: int  # 1, 2, or 3
    critical: bool = False
    kill_command: Optional[str] = None
    verify_command: Optional[str] = None


@dataclass
class KillEvent:
    """Record of kill switch activation."""

    timestamp: datetime
    level: ShutdownLevel
    reason: str
    targets_killed: List[str]
    initiated_by: str
    success: bool
    duration_seconds: float
