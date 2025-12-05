"""Trigger Validation Mixin - ESGT trigger checks and node recruitment."""

from __future__ import annotations

import time
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .models import SalienceScore
    from .coordinator import ESGTCoordinator


class TriggerValidationMixin:
    """Mixin providing trigger validation and node recruitment for ESGT."""

    async def _check_triggers(
        self: "ESGTCoordinator", salience: "SalienceScore"
    ) -> tuple[bool, str]:
        """Check if all trigger conditions are met. Returns (success, failure_reason)."""
        # Salience check
        if not self.triggers.check_salience(salience):
            return (
                False,
                f"Salience too low "
                f"({salience.compute_total():.2f} < {self.triggers.min_salience:.2f})",
            )

        # Resource check
        tig_metrics = self.tig.get_metrics()
        tig_latency = tig_metrics.avg_latency_us / 1000.0  # Convert to ms
        available_nodes = sum(
            1
            for node in self.tig.nodes.values()
            if node.node_state.value in ["active", "esgt_mode"]
        )
        cpu_capacity = 0.60  # Simulated - would query actual metrics

        if not self.triggers.check_resources(
            tig_latency_ms=tig_latency,
            available_nodes=available_nodes,
            cpu_capacity=cpu_capacity,
        ):
            return (
                False,
                f"Insufficient resources "
                f"(nodes={available_nodes}, latency={tig_latency:.1f}ms)",
            )

        # Temporal gating
        time_since_last = (
            time.time() - self.last_esgt_time if self.last_esgt_time > 0 else float("inf")
        )
        recent_count = sum(
            1 for e in self.event_history[-10:] if time.time() - e.timestamp_start < 1.0
        )

        if not self.triggers.check_temporal_gating(time_since_last, recent_count):
            return (
                False,
                f"Refractory period violation "
                f"(time_since_last={time_since_last * 1000:.1f}ms < "
                f"{self.triggers.refractory_period_ms:.1f}ms)",
            )

        # Arousal check (simulated - would query MCEA)
        arousal = 0.70  # Simulated
        if not self.triggers.check_arousal(arousal):
            return (
                False,
                f"Arousal too low ({arousal:.2f} < {self.triggers.min_arousal_level:.2f})",
            )

        return True, ""

    async def _recruit_nodes(
        self: "ESGTCoordinator", content: dict[str, Any]
    ) -> set[str]:
        """
        Recruit participating nodes for ESGT.

        Selection based on:
        - Relevance to content
        - Current load
        - Connectivity quality
        """
        recruited: set[str] = set()

        for node_id, node in self.tig.nodes.items():
            # For now, recruit all active nodes
            # In full implementation, would use content-based selection
            if node.node_state.value in ["active", "esgt_mode"]:
                recruited.add(node_id)

        return recruited

    def _build_topology(
        self: "ESGTCoordinator", node_ids: set[str]
    ) -> dict[str, list[str]]:
        """Build connectivity topology for Kuramoto network."""
        topology: dict[str, list[str]] = {}

        for node_id in node_ids:
            node = self.tig.nodes.get(node_id)
            if node:
                # Get neighbors that are also participating
                neighbors = [
                    conn.remote_node_id
                    for conn in node.connections.values()
                    if conn.active and conn.remote_node_id in node_ids
                ]
                topology[node_id] = neighbors

        return topology
