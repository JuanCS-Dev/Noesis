"""
Main Kill Switch Class.

Emergency shutdown and containment mechanisms.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .audit import AuditMixin
from .deadman_switch import DeadManMixin
from .models import KillEvent, KillTarget, ShutdownLevel
from .shutdown_methods import ShutdownMixin

logger = logging.getLogger(__name__)


class KillSwitch(ShutdownMixin, DeadManMixin, AuditMixin):
    """
    Emergency kill switch for Reactive Fabric.

    Implements multiple levels of shutdown urgency.
    """

    def __init__(self, require_confirmation: bool = True) -> None:
        """
        Initialize kill switch.

        Args:
            require_confirmation: Require confirmation for non-emergency kills
        """
        self.require_confirmation = require_confirmation
        self._armed = False
        self._targets: Dict[str, KillTarget] = {}
        self._kill_history: List[KillEvent] = []
        self._callbacks: List[Callable] = []

        # Dead man's switch
        self._deadmans_active = False
        self._deadmans_task: Optional[asyncio.Task] = None
        self._last_heartbeat = time.time()

        # Audit log
        self._audit_file = Path("/var/log/reactive_fabric/kill_switch.log")

    def arm(self, authorization_code: str) -> bool:
        """
        Arm the kill switch.

        Args:
            authorization_code: Security code to arm

        Returns:
            True if armed successfully
        """
        # Verify authorization
        expected_code = os.getenv("KILL_SWITCH_AUTH_CODE", "VERTICE-EMERGENCY-2025")

        if authorization_code != expected_code:
            logger.error("Invalid authorization code for kill switch")
            self._audit_event("ARM_FAILED", {"reason": "invalid_code"})
            return False

        self._armed = True
        logger.warning("KILL SWITCH ARMED - Emergency shutdown ready")
        self._audit_event("ARMED", {"timestamp": datetime.now().isoformat()})
        return True

    def disarm(self) -> bool:
        """Disarm the kill switch."""
        if not self._armed:
            return False

        self._armed = False
        logger.info("Kill switch disarmed")
        self._audit_event("DISARMED", {"timestamp": datetime.now().isoformat()})
        return True

    def register_target(self, target: KillTarget) -> None:
        """Register a component that can be killed."""
        self._targets[target.id] = target
        logger.debug("Registered kill target: %s (layer %d)", target.name, target.layer)

    def activate(
        self,
        level: ShutdownLevel,
        reason: str,
        initiated_by: str,
        layer: Optional[int] = None,
    ) -> KillEvent:
        """
        ACTIVATE THE KILL SWITCH.

        Args:
            level: Shutdown urgency level
            reason: Reason for activation
            initiated_by: Who/what initiated the kill
            layer: Specific layer to kill (None = all)

        Returns:
            KillEvent record
        """
        if not self._armed and level != ShutdownLevel.NUCLEAR:
            logger.error("Kill switch not armed, activation blocked")
            return KillEvent(
                timestamp=datetime.now(),
                level=level,
                reason=reason,
                targets_killed=[],
                initiated_by=initiated_by,
                success=False,
                duration_seconds=0,
            )

        start_time = time.time()
        killed_targets: List[str] = []

        logger.critical(
            "KILL SWITCH ACTIVATED - Level: %s, Reason: %s", level.value, reason
        )
        self._audit_event(
            "ACTIVATED",
            {
                "level": level.value,
                "reason": reason,
                "initiated_by": initiated_by,
                "layer": layer,
            },
        )

        try:
            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback(level, reason)
                except Exception as e:
                    logger.error("Callback error: %s", e)

            # Select targets
            targets = self._select_targets(layer)

            # Execute kill based on level
            if level == ShutdownLevel.GRACEFUL:
                killed_targets = self._graceful_shutdown(targets)
            elif level == ShutdownLevel.IMMEDIATE:
                killed_targets = self._immediate_shutdown(targets)
            elif level == ShutdownLevel.EMERGENCY:
                killed_targets = self._emergency_shutdown(targets)
            elif level == ShutdownLevel.NUCLEAR:
                killed_targets = self._nuclear_shutdown(targets)

            success = len(killed_targets) == len(targets)

        except Exception as e:
            logger.error("Kill switch activation error: %s", e)
            success = False

        # Record event
        duration = time.time() - start_time
        event = KillEvent(
            timestamp=datetime.now(),
            level=level,
            reason=reason,
            targets_killed=killed_targets,
            initiated_by=initiated_by,
            success=success,
            duration_seconds=duration,
        )

        self._kill_history.append(event)
        self._audit_event(
            "COMPLETED",
            {
                "level": level.value,
                "targets_killed": len(killed_targets),
                "duration": duration,
                "success": success,
            },
        )

        return event

    def _select_targets(self, layer: Optional[int]) -> List[KillTarget]:
        """Select targets based on layer."""
        if layer is None:
            return list(self._targets.values())

        return [t for t in self._targets.values() if t.layer == layer]

    def register_callback(self, callback: Callable) -> None:
        """Register callback for kill switch activation."""
        self._callbacks.append(callback)

    def get_status(self) -> Dict[str, Any]:
        """Get kill switch status."""
        return {
            "armed": self._armed,
            "targets_registered": len(self._targets),
            "deadmans_active": self._deadmans_active,
            "last_heartbeat": self._last_heartbeat if self._deadmans_active else None,
            "kill_history": len(self._kill_history),
            "last_activation": (
                self._kill_history[-1].timestamp.isoformat()
                if self._kill_history
                else None
            ),
        }
