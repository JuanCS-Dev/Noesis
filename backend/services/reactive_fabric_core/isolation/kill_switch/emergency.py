"""
Emergency Shutdown Coordinator.

High-level orchestration of kill switches across all layers.
"""

from __future__ import annotations

import logging
import time
from typing import Dict

from .models import ShutdownLevel
from .switch import KillSwitch

logger = logging.getLogger(__name__)


class EmergencyShutdown:
    """
    High-level emergency shutdown coordinator.

    Orchestrates kill switches across all layers.
    """

    def __init__(self) -> None:
        """Initialize emergency shutdown system."""
        self.kill_switches: Dict[int, KillSwitch] = {}

        # Create kill switch for each layer
        for layer in [1, 2, 3]:
            self.kill_switches[layer] = KillSwitch(
                require_confirmation=(layer == 1)  # L1 requires confirmation
            )

    def containment_breach(self, source_layer: int) -> None:
        """
        CONTAINMENT BREACH DETECTED.

        Emergency response to prevent propagation.

        Args:
            source_layer: Layer where breach detected
        """
        logger.critical("CONTAINMENT BREACH in Layer %d", source_layer)

        # Immediate isolation
        if source_layer == 3:
            # L3 breach - kill L3, isolate L2
            self.kill_switches[3].activate(
                level=ShutdownLevel.IMMEDIATE,
                reason="L3 containment breach",
                initiated_by="BREACH_DETECTOR",
                layer=3,
            )

        elif source_layer == 2:
            # L2 breach - kill L2 and L3, protect L1
            self.kill_switches[2].activate(
                level=ShutdownLevel.EMERGENCY,
                reason="L2 containment breach",
                initiated_by="BREACH_DETECTOR",
                layer=2,
            )
            self.kill_switches[3].activate(
                level=ShutdownLevel.IMMEDIATE,
                reason="L2 breach cascade",
                initiated_by="BREACH_DETECTOR",
                layer=3,
            )

        elif source_layer == 1:
            # L1 breach - CATASTROPHIC - nuclear option
            logger.critical("LAYER 1 BREACH - NUCLEAR SHUTDOWN")
            for layer in [3, 2, 1]:
                self.kill_switches[layer].activate(
                    level=ShutdownLevel.NUCLEAR,
                    reason="L1 CATASTROPHIC BREACH",
                    initiated_by="BREACH_DETECTOR",
                    layer=layer,
                )

    def controlled_shutdown(self, reason: str = "Maintenance") -> None:
        """Controlled shutdown of all layers."""
        for layer in [3, 2, 1]:  # Shutdown from least to most critical
            self.kill_switches[layer].activate(
                level=ShutdownLevel.GRACEFUL,
                reason=reason,
                initiated_by="ADMINISTRATOR",
                layer=layer,
            )
            time.sleep(5)  # Stagger shutdowns
