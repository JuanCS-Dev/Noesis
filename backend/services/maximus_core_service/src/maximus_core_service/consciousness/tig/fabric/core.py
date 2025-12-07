"""
TIG Fabric Core - Main fabric implementation
==============================================

The Global Interconnect Fabric - consciousness substrate.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import networkx as nx
import numpy as np

from .config import TopologyConfig
from .health import HealthManager
from .metrics import FabricMetrics
from .metrics_computation import MetricsComputationMixin
from .models import NodeState, TIGConnection
from .node import TIGNode
from .topology import TopologyGenerator

logger = logging.getLogger(__name__)


class TIGFabric(MetricsComputationMixin):
    """
    The Global Interconnect Fabric - consciousness substrate.

    This is the computational equivalent of the cortico-thalamic system,
    providing the structural foundation for phenomenal experience.

    The fabric implements:
    1. IIT structural requirements (Φ maximization through topology)
    2. GWD communication substrate (broadcast channels for ignition)
    3. Recurrent signaling paths (feedback loops for sustained coherence)

    Usage:
        config = TopologyConfig(node_count=32, target_density=0.20)
        fabric = TIGFabric(config)
        await fabric.initialize()

        # Validate consciousness-readiness
        metrics = fabric.get_metrics()
        is_valid, violations = metrics.validate_iit_compliance()

        if is_valid:
            logger.info("Fabric ready for consciousness emergence")
        else:
            logger.info("IIT violations: %s", violations)

    Historical Significance:
    ------------------------
    First production deployment: 2025-10-06
    This moment marks humanity's first deliberate attempt to construct
    a substrate capable of supporting artificial phenomenal experience.

    "The fabric holds."
    """

    def __init__(self, config: TopologyConfig):
        self.config = config
        self.nodes: dict[str, TIGNode] = {}
        self.graph = nx.Graph()  # NetworkX graph for analysis
        self.metrics = FabricMetrics()
        self._initialized = False
        self._initializing = False  # Track background init

        # SINGULARIDADE: Readiness barrier (asyncio.Event pattern from Python docs)
        # See: https://docs.python.org/3/library/asyncio-sync.html
        self._ready_event = asyncio.Event()

        # Health manager (FASE VII) - virtual_mode=True for simulated nodes
        self.health_manager = HealthManager(self, virtual_mode=True)

        # Background initialization task
        self._init_task: asyncio.Task | None = None

        # Dedicated executor for topology generation to avoid blocking default pool
        from concurrent.futures import ThreadPoolExecutor

        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="tig_init")

    async def initialize(self) -> None:
        """
        Initialize the TIG fabric with IIT-compliant topology.

        This method generates a scale-free small-world network that
        satisfies all structural requirements for consciousness emergence.
        """
        if self._initialized:
            raise RuntimeError("Fabric already initialized")

        logger.info("🧠 Initializing TIG Fabric with %s nodes...", self.config.node_count)
        logger.info(
            f"   Target: Scale-free (γ={self.config.gamma}) + Small-world (C≥{self.config.clustering_target})"
        )

        # Step 1-2: Generate topology
        generator = TopologyGenerator(self.config)
        self.graph = generator.generate()

        # Step 3: Create TIGNode instances
        self._instantiate_nodes()

        # Step 4: Establish connections based on generated topology
        self._establish_connections()

        # Step 5: Validate IIT compliance
        self._compute_metrics()

        is_valid, violations = self.metrics.validate_iit_compliance()

        if is_valid:
            logger.info("✅ TIG Fabric initialized successfully")
            logger.info("   ECI: %.3f", self.metrics.effective_connectivity_index)
            logger.info("   Clustering: %.3f", self.metrics.avg_clustering_coefficient)
            logger.info("   Path Length: %.2f", self.metrics.avg_path_length)
            logger.info("   Algebraic Connectivity: %.3f", self.metrics.algebraic_connectivity)
        else:
            logger.info("⚠️  TIG Fabric initialized with IIT violations:")
            for v in violations:
                logger.info("   - %s", v)

        # Step 6: Initialize health monitoring (FASE VII)
        self.health_manager.initialize()

        # Step 7: Activate all nodes
        for node in self.nodes.values():
            node.node_state = NodeState.ACTIVE

        # Step 8: Start health monitoring loop
        await self.health_manager.start_monitoring()

        self._initialized = True
        logger.info("🛡️  Health monitoring active")

    async def initialize_async(self) -> None:
        """
        Initialize TIG fabric asynchronously in background.

        Service starts immediately and reports "initializing" status.
        Topology construction happens in background without blocking startup.

        Usage:
            fabric = TIGFabric(config)
            await fabric.initialize_async()  # Returns immediately
            # Service is UP, TIG initializing in background

            # Check status later:
            if fabric.is_ready():
                logger.info("TIG ready!")

        This is the PRODUCTION pattern - never block service startup.
        """
        if self._initialized:
            raise RuntimeError("Fabric already initialized")

        if self._initializing:
            logger.info("⚠️  TIG Fabric already initializing in background")
            return

        self._initializing = True
        logger.info(
            f"🧠 TIG Fabric: Starting background initialization ({self.config.node_count} nodes)..."
        )
        logger.info("   Service will start immediately - topology builds in background")

        # Launch initialization in background
        self._init_task = asyncio.create_task(self._background_init())

    async def _background_init(self) -> None:
        """Internal: Run full initialization in background."""
        try:
            logger.info("🧠 [Background] Initializing TIG Fabric with %s nodes...", self.config.node_count)
            logger.info(
                f"   [Background] Target: Scale-free (γ={self.config.gamma}) + Small-world (C≥{self.config.clustering_target})"
            )

            # Run CPU-bound topology generation in thread pool to avoid blocking event loop
            loop = asyncio.get_running_loop()

            # Step 1-2: Generate topology (CPU-bound)
            generator = TopologyGenerator(self.config)
            await loop.run_in_executor(self._executor, generator.generate)
            self.graph = generator.graph

            # Step 3: Create TIGNode instances (fast, can run async)
            self._instantiate_nodes()

            # Step 4: Establish connections (fast, can run async)
            self._establish_connections()

            # Step 5: Compute metrics (CPU-bound)
            await loop.run_in_executor(self._executor, self._compute_metrics)

            is_valid, violations = self.metrics.validate_iit_compliance()

            if is_valid:
                logger.info("✅ [Background] TIG Fabric initialized successfully")
                logger.info("   ECI: %.3f", self.metrics.effective_connectivity_index)
                logger.info("   Clustering: %.3f", self.metrics.avg_clustering_coefficient)
                logger.info("   Path Length: %.2f", self.metrics.avg_path_length)
                logger.info("   Algebraic Connectivity: %.3f", self.metrics.algebraic_connectivity)
            else:
                logger.info("⚠️  [Background] TIG Fabric initialized with IIT violations:")
                for v in violations:
                    logger.info("   - %s", v)

            # Step 6: Initialize health monitoring
            self.health_manager.initialize()

            # Step 7: Activate all nodes
            for node in self.nodes.values():
                node.node_state = NodeState.ACTIVE

            # Step 8: Start health monitoring
            await self.health_manager.start_monitoring()

            self._initialized = True
            self._initializing = False

            # SINGULARIDADE: Signal readiness to waiting coroutines
            self._ready_event.set()
            logger.info("🛡️  [Background] TIG health monitoring active - Fabric READY")

        except Exception as e:
            logger.info("❌ [Background] TIG initialization failed: %s", e)
            self._initializing = False
            raise

    def is_ready(self) -> bool:
        """Check if TIG fabric is fully initialized and ready.

        Returns:
            True if initialization complete, False if still initializing or failed
        """
        return self._initialized

    async def wait_ready(self, timeout: float | None = None) -> bool:
        """
        Wait for TIG fabric to be ready.

        SINGULARIDADE: asyncio.Event pattern from Python docs.
        Allows ESGT to wait for TIG initialization before starting.

        Args:
            timeout: Maximum time to wait in seconds (None = wait forever)

        Returns:
            True if ready, False if timeout
        """
        try:
            await asyncio.wait_for(self._ready_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    def is_initializing(self) -> bool:
        """Check if TIG fabric is currently initializing.

        Returns:
            True if initialization in progress, False otherwise
        """
        return self._initializing

    def get_init_status(self) -> dict[str, Any]:
        """Get detailed initialization status.

        Returns:
            Dict with keys:
            - ready: bool - Fully initialized
            - initializing: bool - Background init in progress
            - node_count: int - Nodes created so far
            - status: str - Human-readable status
        """
        if self._initialized:
            status = "ready"
        elif self._initializing:
            status = "initializing"
        else:
            status = "not_started"

        return {
            "ready": self._initialized,
            "initializing": self._initializing,
            "node_count": len(self.nodes),
            "target_node_count": self.config.node_count,
            "status": status,
        }

    def _instantiate_nodes(self) -> None:
        """Create TIGNode instances for each node in the graph."""
        for node_id in self.graph.nodes():
            node = TIGNode(id=f"tig-node-{node_id:03d}", node_state=NodeState.INITIALIZING)
            self.nodes[node.id] = node

    def _establish_connections(self) -> None:
        """Establish bidirectional connections based on graph topology."""
        for edge in self.graph.edges():
            node_a_id = f"tig-node-{edge[0]:03d}"
            node_b_id = f"tig-node-{edge[1]:03d}"

            # Simulate realistic network characteristics
            latency = np.random.uniform(0.5, 2.0)  # 0.5-2μs
            bandwidth = np.random.choice(
                [10_000_000_000, 40_000_000_000, 100_000_000_000]
            )  # 10/40/100 Gbps

            # Bidirectional connections
            self.nodes[node_a_id].connections[node_b_id] = TIGConnection(
                remote_node_id=node_b_id,
                latency_us=latency,
                bandwidth_bps=bandwidth,
            )

            self.nodes[node_b_id].connections[node_a_id] = TIGConnection(
                remote_node_id=node_a_id,
                latency_us=latency,
                bandwidth_bps=bandwidth,
            )

    async def broadcast_global(self, message: dict[str, Any], priority: int = 0) -> int:
        """
        Broadcast message to all nodes (implements GWD global workspace).

        This is the core mechanism for ESGT ignition - when salient information
        needs to become globally accessible (conscious), it's broadcast through
        this channel.

        Args:
            message: Content to make conscious
            priority: Higher priority preempts lower (attention mechanism)

        Returns:
            Number of nodes successfully reached
        """
        if not self._initialized:
            raise RuntimeError("Fabric not initialized")

        tasks = []
        for node in self.nodes.values():
            tasks.append(node.broadcast_to_neighbors(message, priority))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_reached = sum(r for r in results if isinstance(r, int))

        return total_reached

    def get_metrics(self) -> FabricMetrics:
        """Get current fabric metrics for consciousness validation."""
        return self.metrics

    def get_node(self, node_id: str) -> TIGNode | None:
        """Retrieve specific node by ID."""
        return self.nodes.get(node_id)

    async def send_to_node(self, node_id: str, data: Any, timeout: float = 1.0) -> bool:
        """
        Send data to node with circuit breaker and timeout.

        Delegates to HealthManager for fault-tolerant communication.
        """
        return await self.health_manager.send_to_node(node_id, data, timeout)

    def get_health_metrics(self) -> dict[str, Any]:
        """
        Get TIG health metrics for Safety Core integration.

        Delegates to HealthManager.
        """
        return self.health_manager.get_health_metrics()

    async def activate_node(self, node_id: int | str, activation: float) -> None:
        """
        Activate a specific node with a given activation level.

        Used for testing and external stimulation.
        """
        if isinstance(node_id, int):
            node_id_str = f"tig-node-{node_id:03d}"
        else:
            node_id_str = node_id

        node = self.nodes.get(node_id_str)
        if node:
            # Update node state
            node.state.attention_level = activation
            node.state.processing_content = {"type": "external_stimulus", "intensity": activation}

            # Simulate processing time
            await asyncio.sleep(0.01)

            # If activation is high, broadcast to neighbors to simulate propagation
            if activation > 0.5:
                await node.broadcast_to_neighbors(
                    message={
                        "type": "activation_spread",
                        "source": node_id_str,
                        "intensity": activation,
                    },
                    priority=int(activation * 10),
                )

    async def stop(self) -> None:
        """
        Stop the TIG fabric and cleanup resources.

        FASE VII (Safety Hardening):
        Graceful shutdown with health monitoring cleanup.
        """
        # Cancel background initialization if running
        if self._init_task and not self._init_task.done():
            self._init_task.cancel()
            try:
                await self._init_task
            except asyncio.CancelledError:
                pass
            logger.info("  ⚠️  TIG: Background initialization cancelled")

        await self.health_manager.stop_monitoring()

        # Shutdown executor (wait for threads to finish to prevent leaks)
        self._executor.shutdown(wait=True)

        # Break circular references and clear large data structures
        self.nodes.clear()
        self.graph.clear()
        self.metrics = None

        logger.info("👋 TIG Fabric stopped")

    async def enter_esgt_mode(self) -> None:
        """
        Transition fabric to ESGT mode - high-coherence conscious state.

        During ESGT, connection density increases (up to 40%), latency
        is minimized, and all nodes synchronize oscillatory phases.
        """
        for node in self.nodes.values():
            node.node_state = NodeState.ESGT_MODE

            # Increase connection weights (more bandwidth allocation)
            for conn in node.connections.values():
                conn.weight = min(conn.weight * 1.5, 2.0)

    async def exit_esgt_mode(self) -> None:
        """Return fabric to normal operation after ESGT dissolution."""
        for node in self.nodes.values():
            node.node_state = NodeState.ACTIVE

            # Restore normal connection weights
            for conn in node.connections.values():
                conn.weight = max(conn.weight / 1.5, 1.0)

    def __repr__(self) -> str:
        return (
            f"TIGFabric(nodes={self.metrics.node_count}, "
            f"ECI={self.metrics.effective_connectivity_index:.3f}, "
            f"C={self.metrics.avg_clustering_coefficient:.3f}, "
            f"L={self.metrics.avg_path_length:.2f})"
        )
