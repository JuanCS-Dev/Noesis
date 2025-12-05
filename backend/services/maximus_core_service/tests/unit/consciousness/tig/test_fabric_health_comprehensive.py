"""
Comprehensive Tests for TIG Fabric Health Manager
==================================================

Target: 80%+ coverage for consciousness/tig/fabric/health.py
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from consciousness.tig.fabric.config import TopologyConfig
from consciousness.tig.fabric.core import TIGFabric
from consciousness.tig.fabric.health import HealthManager
from consciousness.tig.fabric.models import CircuitBreaker, NodeHealth, NodeState


class TestHealthManagerInit:
    """Test HealthManager initialization."""

    @pytest.mark.asyncio
    async def test_init_with_fabric(self):
        """Test initialization with TIGFabric."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        manager = fabric.health_manager
        assert manager is not None
        assert manager.fabric == fabric
        await fabric.stop()

    @pytest.mark.asyncio
    async def test_initialize_creates_health_tracking(self):
        """Test initialize creates health tracking for nodes."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        manager = fabric.health_manager
        
        assert len(manager.node_health) == 10
        await fabric.stop()


class TestHealthManagerMonitoring:
    """Test health monitoring functionality."""

    @pytest.mark.asyncio
    async def test_health_monitoring_runs(self):
        """Test health monitoring is active after init."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        manager = fabric.health_manager
        assert manager._running is True
        
        await fabric.stop()
        
        # Should be stopped
        assert manager._running is False


class TestHealthManagerSendToNode:
    """Test send_to_node with circuit breaker."""

    @pytest.mark.asyncio
    async def test_send_to_node_success(self):
        """Test successful send to node."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        manager = fabric.health_manager
        node_id = list(fabric.nodes.keys())[0]
        
        result = await manager.send_to_node(node_id, {"test": "data"})
        
        assert result is True
        await fabric.stop()

    @pytest.mark.asyncio
    async def test_send_to_node_with_timeout(self):
        """Test send with custom timeout."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        manager = fabric.health_manager
        node_id = list(fabric.nodes.keys())[0]
        
        result = await manager.send_to_node(node_id, {"test": "data"}, timeout=2.0)
        
        assert result is True
        await fabric.stop()


class TestHealthManagerNodeIsolation:
    """Test node isolation and reintegration."""

    @pytest.mark.asyncio
    async def test_isolate_dead_node(self):
        """Test isolating a dead node."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        manager = fabric.health_manager
        node_id = list(fabric.nodes.keys())[0]
        
        # Isolate the node
        await manager._isolate_dead_node(node_id)
        
        # Node should be in isolated state
        health = manager.node_health.get(node_id)
        if health:
            assert health.isolated is True
        await fabric.stop()

    @pytest.mark.asyncio
    async def test_reintegrate_node(self):
        """Test reintegrating a recovered node."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        manager = fabric.health_manager
        node_id = list(fabric.nodes.keys())[0]
        
        # Isolate then reintegrate
        await manager._isolate_dead_node(node_id)
        await manager._reintegrate_node(node_id)
        
        # Node should be back to healthy
        health = manager.node_health.get(node_id)
        if health:
            assert health.isolated is False
        await fabric.stop()


class TestHealthManagerTopologyRepair:
    """Test topology repair around dead nodes."""

    @pytest.mark.asyncio
    async def test_repair_topology_around_dead_node(self):
        """Test repairing topology when node dies."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        manager = fabric.health_manager
        node_id = list(fabric.nodes.keys())[0]
        
        # Repair topology
        manager._repair_topology_around_dead_node(node_id)
        
        # Should still have connectivity
        assert fabric.graph.number_of_nodes() >= 9
        await fabric.stop()


class TestHealthManagerNetworkPartition:
    """Test network partition detection."""

    @pytest.mark.asyncio
    async def test_detect_network_partition_no_partition(self):
        """Test partition detection with healthy network."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        manager = fabric.health_manager
        
        is_partitioned = manager._detect_network_partition()
        
        assert is_partitioned is False
        await fabric.stop()


class TestHealthManagerMetrics:
    """Test health metrics retrieval."""

    @pytest.mark.asyncio
    async def test_get_health_metrics(self):
        """Test getting comprehensive health metrics."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        manager = fabric.health_manager
        
        metrics = manager.get_health_metrics()
        
        assert isinstance(metrics, dict)
        assert "total_nodes" in metrics
        assert "healthy_nodes" in metrics
        await fabric.stop()

    @pytest.mark.asyncio
    async def test_get_health_metrics_values(self):
        """Test health metrics have correct values."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        manager = fabric.health_manager
        
        metrics = manager.get_health_metrics()
        
        assert metrics["total_nodes"] == 10
        assert metrics["healthy_nodes"] <= 10
        await fabric.stop()


class TestHealthManagerSendFailure:
    """Test send failure handling."""

    @pytest.mark.asyncio
    async def test_handle_send_failure(self):
        """Test handling send failure."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        manager = fabric.health_manager
        node_id = list(fabric.nodes.keys())[0]
        
        # Trigger failure handling
        manager._handle_send_failure(node_id, "Test failure")
        
        # Health should be updated
        health = manager.node_health.get(node_id)
        if health:
            assert health.failures >= 1
        await fabric.stop()


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker starts closed."""
        cb = CircuitBreaker()
        assert cb.state == "closed"
        assert cb.failures == 0

    def test_circuit_breaker_is_open_initially_false(self):
        """Test is_open returns False initially."""
        cb = CircuitBreaker()
        assert cb.is_open() is False

    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures."""
        cb = CircuitBreaker(failure_threshold=3)
        
        for i in range(3):
            cb.record_failure()
        
        assert cb.state == "open"
        assert cb.is_open() is True

    def test_circuit_breaker_resets_on_success_half_open(self):
        """Test circuit breaker resets on success when half-open."""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.01)
        
        # Open the breaker
        for i in range(3):
            cb.record_failure()
        
        assert cb.state == "open"
        
        # Wait for recovery timeout
        import time
        time.sleep(0.02)
        
        # Check should transition to half_open
        cb.is_open()
        
        # Record success should close
        cb.record_success()
        
        assert cb.state == "closed" or cb.failures == 0

    def test_circuit_breaker_open_method(self):
        """Test explicit open method."""
        cb = CircuitBreaker()
        cb.open()
        assert cb.state == "open"

    def test_circuit_breaker_repr(self):
        """Test repr."""
        cb = CircuitBreaker()
        repr_str = repr(cb)
        assert "CircuitBreaker" in repr_str
        assert "closed" in repr_str


class TestNodeHealth:
    """Test NodeHealth dataclass."""

    def test_node_health_creation(self):
        """Test NodeHealth creation."""
        health = NodeHealth(node_id="test-node")
        assert health.node_id == "test-node"
        assert health.failures == 0
        assert health.isolated is False
        assert health.degraded is False

    def test_node_health_is_healthy(self):
        """Test is_healthy method."""
        health = NodeHealth(node_id="test-node")
        assert health.is_healthy() is True
        
    def test_node_health_is_healthy_isolated(self):
        """Test isolated node is not healthy."""
        health = NodeHealth(node_id="test-node", isolated=True)
        assert health.is_healthy() is False

    def test_node_health_is_healthy_degraded(self):
        """Test degraded node is not healthy."""
        health = NodeHealth(node_id="test-node", degraded=True)
        assert health.is_healthy() is False

    def test_node_health_is_healthy_many_failures(self):
        """Test node with many failures is not healthy."""
        health = NodeHealth(node_id="test-node", failures=5)
        assert health.is_healthy() is False
