"""Phase Operations Mixin - ESGT sustain and dissolve logic."""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import ESGTEvent
    from .coordinator import ESGTCoordinator


class PhaseOperationsMixin:
    """Mixin providing ESGT phase operations for sustain and dissolve."""

    async def _sustain_coherence(
        self: "ESGTCoordinator",
        event: "ESGTEvent",
        duration_ms: float,
        topology: dict[str, list[str]],
    ) -> None:
        """
        Sustain synchronization for target duration.

        Continuously updates Kuramoto dynamics and monitors coherence.
        """
        start_time = time.time()
        duration_s = duration_ms / 1000.0

        while (time.time() - start_time) < duration_s:
            # Update network
            self.kuramoto.update_network(topology, dt=0.005)

            # Record coherence
            coherence = self.kuramoto.get_coherence()
            if coherence:
                event.coherence_history.append(coherence.order_parameter)

            # Small yield
            await asyncio.sleep(0.005)

    async def _dissolve_event(self: "ESGTCoordinator", event: "ESGTEvent") -> None:
        """Gracefully dissolve synchronization."""
        # Reduce coupling strength gradually
        for osc in self.kuramoto.oscillators.values():
            osc.config.coupling_strength *= 0.5

        # Continue for 50ms with reduced coupling
        topology = self._build_topology(event.participating_nodes)

        for _ in range(10):  # 10 x 5ms = 50ms
            self.kuramoto.update_network(topology, dt=0.005)
            await asyncio.sleep(0.005)

        # Reset oscillators
        self.kuramoto.reset_all()
