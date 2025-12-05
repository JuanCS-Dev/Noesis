"""
TIG Fabric Health Management
==============================

Health monitoring and fault tolerance for TIG nodes.
FASE VII (Safety Hardening) components.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any

import networkx as nx
import numpy as np

from .models import CircuitBreaker, NodeHealth, NodeState, TIGConnection

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .core import TIGFabric



class HealthManager:
    """
    Manages health monitoring and fault tolerance for TIG fabric.

    FASE VII (Safety Hardening):
    - Monitors node health continuously
    - Isolates dead/problematic nodes
    - Repairs topology around failures
    - Implements circuit breaker pattern
    """

    def __init__(self, fabric: TIGFabric):
        self.fabric = fabric
        self.node_health: dict[str, NodeHealth] = {}
        self.circuit_breakers: dict[str, CircuitBreaker] = {}

        # Configuration
        self.dead_node_timeout = 5.0  # seconds
        self.max_failures_before_isolation = 3

        # Runtime state
        self._running = False
        self._health_monitor_task: asyncio.Task | None = None

    def initialize(self) -> None:
        """Initialize health tracking for all nodes."""
        for node_id in self.fabric.nodes.keys():
            self.node_health[node_id] = NodeHealth(node_id=node_id)
            self.circuit_breakers[node_id] = CircuitBreaker()

    async def start_monitoring(self) -> None:
        """Start health monitoring loop."""
        self._running = True
        self._health_monitor_task = asyncio.create_task(self._health_monitoring_loop())

    async def stop_monitoring(self) -> None:
        """Stop health monitoring loop."""
        self._running = False

        if self._health_monitor_task:
            self._health_monitor_task.cancel()
            try:
                await self._health_monitor_task
            except asyncio.CancelledError:
                pass

        # Break circular reference
        self.fabric = None
        self.node_health.clear()
        self.circuit_breakers.clear()

    async def _health_monitoring_loop(self) -> None:
        """
        Monitor health of all nodes continuously.

        FASE VII (Safety Hardening):
        Detects dead nodes, triggers isolation, and monitors for recovery.
        """
        while self._running:
            current_time = time.time()

            for node_id, health in self.node_health.items():
                try:
                    # Check if node is dead (not seen within timeout)
                    if current_time - health.last_seen > self.dead_node_timeout:
                        if not health.isolated:
                            await self._isolate_dead_node(node_id)

                    # Check if isolated node should be reintegrated
                    elif health.isolated and health.failures == 0:
                        await self._reintegrate_node(node_id)

                except Exception as e:
                    logger.info("⚠️  Health monitoring error for %s: {e}", node_id)
                    # Continue monitoring other nodes despite errors

            await asyncio.sleep(1.0)  # Check every second

    async def _isolate_dead_node(self, node_id: str) -> None:
        """
        Isolate a dead or problematic node.

        FASE VII (Safety Hardening):
        Removes node from active topology and triggers repair.
        """
        logger.info("🔴 TIG: Isolating dead node %s", node_id)

        # Mark as isolated
        self.node_health[node_id].isolated = True
        node = self.fabric.nodes.get(node_id)
        if node:
            node.node_state = NodeState.OFFLINE

        # Trigger topology repair
        await self._repair_topology_around_dead_node(node_id)

    async def _reintegrate_node(self, node_id: str) -> None:
        """
        Reintegrate a recovered node back into active topology.

        FASE VII (Safety Hardening):
        Brings node back online after recovery.
        """
        logger.info("✅ TIG: Reintegrating recovered node %s", node_id)

        # Mark as active
        self.node_health[node_id].isolated = False
        node = self.fabric.nodes.get(node_id)
        if node:
            node.node_state = NodeState.ACTIVE

        # Reset health tracking
        self.node_health[node_id].last_seen = time.time()

    async def _repair_topology_around_dead_node(self, dead_node_id: str) -> None:
        """
        Repair topology to maintain connectivity after node death.

        FASE VII (Safety Hardening):
        Creates bypass connections between neighbors of dead node.
        """
        dead_node = self.fabric.nodes.get(dead_node_id)
        if not dead_node:
            return

        # Find neighbors of dead node
        neighbors = list(dead_node.connections.keys())

        if len(neighbors) < 2:
            return  # No bypass needed

        # Create bypass connections (connect neighbors to each other)
        bypasses_created = 0
        for i, n1_id in enumerate(neighbors):
            for n2_id in neighbors[i + 1 :]:
                n1 = self.fabric.nodes.get(n1_id)
                n2 = self.fabric.nodes.get(n2_id)

                if n1 and n2 and n2_id not in n1.connections:
                    # Create bidirectional bypass connection
                    latency = np.random.uniform(0.5, 2.0)
                    bandwidth = 10_000_000_000

                    n1.connections[n2_id] = TIGConnection(
                        remote_node_id=n2_id, latency_us=latency, bandwidth_bps=bandwidth
                    )

                    n2.connections[n1_id] = TIGConnection(
                        remote_node_id=n1_id, latency_us=latency, bandwidth_bps=bandwidth
                    )

                    bypasses_created += 1

        if bypasses_created > 0:
            logger.info("  ✓ Created %s bypass connections", bypasses_created)

    async def send_to_node(self, node_id: str, data: Any, timeout: float = 1.0) -> bool:
        """
        Send data to node with circuit breaker and timeout.

        FASE VII (Safety Hardening):
        Production-grade communication with fault tolerance.

        Args:
            node_id: Target node ID
            data: Data to send
            timeout: Timeout in seconds

        Returns:
            True if send successful, False otherwise
        """
        # Check if node is isolated
        health = self.node_health.get(node_id)
        if health and health.isolated:
            return False

        # Check circuit breaker
        breaker = self.circuit_breakers.get(node_id)
        if breaker and breaker.is_open():
            return False

        try:
            # Send with timeout
            async with asyncio.timeout(timeout):
                # In production, would send via actual network
                # For now, simulate network operation
                node = self.fabric.nodes.get(node_id)
                if not node:
                    raise RuntimeError(f"Node {node_id} not found")

                # Simulate successful send
                await asyncio.sleep(0.001)  # 1ms simulated latency

            # Update health (success)
            if health:
                health.last_seen = time.time()
            if breaker:
                breaker.record_success()

            return True

        except TimeoutError:
            logger.info("⚠️  TIG: Send timeout to node %s", node_id)
            return self._handle_send_failure(node_id, "timeout")

        except Exception as e:
            logger.info("⚠️  TIG: Send error to node %s: {e}", node_id)
            return self._handle_send_failure(node_id, str(e))

    def _handle_send_failure(self, node_id: str, reason: str) -> bool:
        """
        Handle node communication failure.

        FASE VII (Safety Hardening):
        Updates health tracking and opens circuit breaker if needed.
        """
        health = self.node_health.get(node_id)
        if health:
            health.failures += 1

            # Open circuit breaker if too many failures
            if health.failures >= self.max_failures_before_isolation:
                breaker = self.circuit_breakers.get(node_id)
                if breaker:
                    breaker.open()
                    logger.info(
                        f"⚠️  TIG: Circuit breaker OPEN for node {node_id} ({health.failures} failures)"
                    )

        return False

    def _detect_network_partition(self) -> bool:
        """
        Detect if network is partitioned (graph disconnected).

        A network partition occurs when nodes split into isolated groups
        that cannot communicate. This is detected via graph connectivity analysis.

        Returns:
            True if network has 2+ disconnected components, False otherwise.
        """
        if len(self.fabric.nodes) < 2:
            return False  # Cannot partition with <2 nodes

        # Build active connectivity graph (exclude isolated nodes)
        active_nodes = [
            node_id
            for node_id, health in self.node_health.items()
            if not health.isolated and node_id in self.fabric.nodes
        ]

        if len(active_nodes) < 2:
            return False  # Not enough active nodes to partition

        # Create subgraph of active nodes
        try:
            active_graph = self.fabric.graph.subgraph(active_nodes)
            num_components = nx.number_connected_components(active_graph)
            return num_components > 1  # Partitioned if 2+ components
        except Exception:
            # If graph analysis fails, assume no partition (fail-safe)
            return False

    def get_health_metrics(self) -> dict[str, Any]:
        """
        Get TIG health metrics for Safety Core integration.

        FASE VII (Safety Hardening):
        Exposes health status for consciousness safety monitoring.

        Returns:
            Dict with health metrics:
            - total_nodes: Total node count
            - healthy_nodes: Active, non-isolated nodes
            - isolated_nodes: Nodes currently isolated
            - degraded_nodes: Nodes in degraded state
            - connectivity: Average connectivity ratio
            - is_partitioned: Network partition detected
        """
        total_nodes = len(self.node_health)
        isolated_nodes = sum(1 for h in self.node_health.values() if h.isolated)
        degraded_nodes = sum(1 for h in self.node_health.values() if h.degraded)
        healthy_nodes = total_nodes - isolated_nodes - degraded_nodes

        # Compute connectivity ratio
        if total_nodes > 0:
            connectivity = healthy_nodes / total_nodes
        else:
            connectivity = 0.0

        # Detect network partition
        is_partitioned = self._detect_network_partition()

        return {
            "total_nodes": total_nodes,
            "healthy_nodes": healthy_nodes,
            "isolated_nodes": isolated_nodes,
            "degraded_nodes": degraded_nodes,
            "connectivity": connectivity,
            "connectivity_ratio": self.fabric.metrics.connectivity_ratio,  # Graph-based connectivity
            "is_partitioned": is_partitioned,
        }
