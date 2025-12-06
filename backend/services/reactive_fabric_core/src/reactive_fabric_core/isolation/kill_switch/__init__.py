"""
Kill Switch Package.

Emergency shutdown and containment mechanisms.
"""

from __future__ import annotations

from .emergency import EmergencyShutdown
from .models import ComponentType, KillEvent, KillTarget, ShutdownLevel
from .switch import KillSwitch

__all__ = [
    "KillSwitch",
    "EmergencyShutdown",
    "ShutdownLevel",
    "ComponentType",
    "KillTarget",
    "KillEvent",
]
