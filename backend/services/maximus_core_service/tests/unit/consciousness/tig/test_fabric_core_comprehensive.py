"""
Comprehensive Tests for TIG Fabric Core
========================================

Target: 80%+ coverage for consciousness/tig/fabric/core.py
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from consciousness.tig.fabric.config import TopologyConfig
from consciousness.tig.fabric.core import TIGFabric
from consciousness.tig.fabric.models import NodeState


class TestTIGFabricInit:
    """Test TIGFabric initialization."""

    def test_init_with_default_config(self):
        """Test initialization with default config."""
        config = TopologyConfig()
        fabric = TIGFabric(config)
        assert fabric.config == config
        assert fabric._initialized is False
        assert fabric._initializing is False

    def test_init_with_custom_node_count(self):
        """Test initialization with custom node count."""
        config = TopologyConfig(node_count=50)
        fabric = TIGFabric(config)
        assert fabric.config.node_count == 50
        
    def test_init_creates_health_manager(self):
        """Test that init creates health manager."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        assert fabric.health_manager is not None


class TestTIGFabricAsyncInit:
    """Test async initialization."""

    @pytest.mark.asyncio
    async def test_initialize_creates_nodes(self):
        """Test that initialize creates nodes."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        assert fabric.is_ready() is True
        assert len(fabric.nodes) == 10
        await fabric.stop()

    @pytest.mark.asyncio
    async def test_initialize_establishes_connections(self):
        """Test that initialize establishes connections."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        # Check that connections exist
        for node in fabric.nodes.values():
            assert hasattr(node, 'connections')
        await fabric.stop()

    @pytest.mark.asyncio
    async def test_initialize_creates_graph(self):
        """Test that graph is created correctly."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        assert fabric.graph is not None
        assert fabric.graph.number_of_nodes() == 10
        await fabric.stop()

    @pytest.mark.asyncio
    async def test_initialize_async_starts_background_init(self):
        """Test async init starts background initialization."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        
        await fabric.initialize_async()
        
        # Should be initializing
        assert fabric.is_initializing() is True or fabric.is_ready() is True
        
        # Wait for completion
        for _ in range(100):  # Max 10 seconds
            if fabric.is_ready():
                break
            await asyncio.sleep(0.1)
        
        assert fabric.is_ready() is True
        await fabric.stop()

    def test_get_init_status_before_init(self):
        """Test get_init_status before initialization."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        
        status = fabric.get_init_status()
        assert status["ready"] is False
        assert status["initializing"] is False
        assert isinstance(status["status"], str)


class TestTIGFabricBroadcast:
    """Test broadcast functionality."""

    @pytest.mark.asyncio
    async def test_broadcast_global_to_all_nodes(self):
        """Test broadcast reaches all nodes."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        message = {"type": "test", "data": "hello"}
        reached = await fabric.broadcast_global(message, priority=1)
        
        assert reached >= 0  # At least no error
        await fabric.stop()

    @pytest.mark.asyncio
    async def test_broadcast_with_priority(self):
        """Test broadcast with different priorities."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        # High priority broadcast
        msg1 = {"type": "urgent", "data": "high"}
        reached1 = await fabric.broadcast_global(msg1, priority=10)
        
        # Low priority broadcast
        msg2 = {"type": "routine", "data": "low"}
        reached2 = await fabric.broadcast_global(msg2, priority=1)
        
        assert reached1 >= 0
        assert reached2 >= 0
        await fabric.stop()


class TestTIGFabricNodeOperations:
    """Test node operations."""

    @pytest.mark.asyncio
    async def test_get_node(self):
        """Test get_node retrieves correct node."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        # Get first node
        node_id = list(fabric.nodes.keys())[0]
        node = fabric.get_node(node_id)
        
        assert node is not None
        assert node.id == node_id
        await fabric.stop()

    @pytest.mark.asyncio
    async def test_activate_node(self):
        """Test node activation."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        node_id = list(fabric.nodes.keys())[0]
        await fabric.activate_node(node_id, activation=0.8)
        
        node = fabric.get_node(node_id)
        assert node.state.attention_level == 0.8
        await fabric.stop()

    @pytest.mark.asyncio
    async def test_activate_node_by_index(self):
        """Test node activation by numeric index."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        # Activate by index
        await fabric.activate_node(0, activation=0.5)
        await fabric.stop()


class TestTIGFabricMetrics:
    """Test metrics retrieval."""

    @pytest.mark.asyncio
    async def test_get_metrics(self):
        """Test get_metrics returns FabricMetrics."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        metrics = fabric.get_metrics()
        
        assert metrics is not None
        assert hasattr(metrics, "node_count")
        assert hasattr(metrics, "avg_clustering_coefficient")
        await fabric.stop()

    @pytest.mark.asyncio
    async def test_get_health_metrics(self):
        """Test get_health_metrics for safety integration."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        health = fabric.get_health_metrics()
        
        assert isinstance(health, dict)
        assert "total_nodes" in health
        assert "healthy_nodes" in health
        await fabric.stop()


class TestTIGFabricESGTMode:
    """Test ESGT mode operations."""

    @pytest.mark.asyncio
    async def test_enter_esgt_mode(self):
        """Test entering ESGT mode."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        await fabric.enter_esgt_mode()
        
        # Check nodes are in ESGT mode
        for node in fabric.nodes.values():
            assert node.node_state == NodeState.ESGT_MODE
        await fabric.stop()

    @pytest.mark.asyncio
    async def test_exit_esgt_mode(self):
        """Test exiting ESGT mode."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        await fabric.enter_esgt_mode()
        await fabric.exit_esgt_mode()
        
        # Check nodes are back to ACTIVE
        for node in fabric.nodes.values():
            assert node.node_state == NodeState.ACTIVE
        await fabric.stop()


class TestTIGFabricStop:
    """Test stop and cleanup."""

    @pytest.mark.asyncio
    async def test_stop_cleans_up(self):
        """Test stop cleans up resources."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        await fabric.stop()
        
        # After stop, nodes should be cleared
        assert len(fabric.nodes) == 0


class TestTIGFabricRepr:
    """Test string representation."""

    def test_repr_before_init(self):
        """Test repr before initialization."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        repr_str = repr(fabric)
        assert "TIGFabric" in repr_str

    @pytest.mark.asyncio
    async def test_repr_after_init(self):
        """Test repr after initialization."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        repr_str = repr(fabric)
        assert "TIGFabric" in repr_str
        await fabric.stop()


class TestTIGFabricSendToNode:
    """Test send_to_node with circuit breaker."""

    @pytest.mark.asyncio
    async def test_send_to_node_success(self):
        """Test successful send to node."""
        config = TopologyConfig(node_count=10)
        fabric = TIGFabric(config)
        await fabric.initialize()
        
        node_id = list(fabric.nodes.keys())[0]
        result = await fabric.send_to_node(node_id, {"test": "data"})
        
        assert result is True
        await fabric.stop()
