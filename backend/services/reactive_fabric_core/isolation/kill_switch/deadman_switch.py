"""
Dead Man's Switch for Kill Switch.

Auto-triggers emergency shutdown if heartbeat stops.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

from .models import ShutdownLevel

logger = logging.getLogger(__name__)


class DeadManMixin:
    """Mixin providing dead man's switch functionality."""

    _deadmans_active: bool
    _deadmans_task: Optional[asyncio.Task]
    _last_heartbeat: float
    _armed: bool

    def activate(
        self,
        level: ShutdownLevel,
        reason: str,
        initiated_by: str,
        layer: Optional[int] = None,
    ):
        """Activate kill switch (implemented in switch.py)."""
        raise NotImplementedError

    async def start_deadmans_switch(self, timeout_seconds: int = 300) -> None:
        """
        Start dead man's switch.

        Auto-triggers if no heartbeat received.

        Args:
            timeout_seconds: Time before auto-trigger
        """
        if self._deadmans_active:
            logger.warning("Dead man's switch already active")
            return

        self._deadmans_active = True
        self._last_heartbeat = time.time()

        async def monitor() -> None:
            while self._deadmans_active:
                elapsed = time.time() - self._last_heartbeat

                if elapsed > timeout_seconds:
                    logger.critical("DEAD MAN'S SWITCH TRIGGERED - No heartbeat")
                    self.activate(
                        level=ShutdownLevel.EMERGENCY,
                        reason="Dead man's switch timeout",
                        initiated_by="DEADMANS_SWITCH",
                    )
                    break

                await asyncio.sleep(10)  # Check every 10 seconds

        self._deadmans_task = asyncio.create_task(monitor())
        logger.info("Dead man's switch active (timeout: %ds)", timeout_seconds)

    def heartbeat(self) -> None:
        """Reset dead man's switch timer."""
        self._last_heartbeat = time.time()

    async def stop_deadmans_switch(self) -> None:
        """Stop dead man's switch."""
        self._deadmans_active = False
        if self._deadmans_task:
            self._deadmans_task.cancel()
            try:
                await self._deadmans_task
            except asyncio.CancelledError:
                pass
