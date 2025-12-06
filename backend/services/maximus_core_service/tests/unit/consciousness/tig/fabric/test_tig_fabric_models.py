"""Tests for tig/fabric/config.py and tig/fabric/models.py"""

import time

from consciousness.tig.fabric.config import TopologyConfig
from consciousness.tig.fabric.models import (
    CircuitBreaker,
    NodeHealth,
    NodeState,
    ProcessingState,
    TIGConnection,
)


class TestTopologyConfig:
    """Test TopologyConfig dataclass."""

    def test_creation_defaults(self):
        """Test creating with defaults."""
        config = TopologyConfig()
        
        assert config.node_count == 16
        assert config.min_degree == 5
        assert config.target_density == 0.20
        assert config.gamma == 2.5
        assert config.clustering_target == 0.75
        assert config.enable_small_world_rewiring is True
        assert config.rewiring_probability == 0.58

    def test_creation_custom(self):
        """Test creating with custom values."""
        config = TopologyConfig(
            node_count=32,
            min_degree=8,
            target_density=0.30,
            gamma=3.0,
        )
        
        assert config.node_count == 32
        assert config.min_degree == 8
        assert config.target_density == 0.30
        assert config.gamma == 3.0

    def test_num_nodes_alias(self):
        """Test num_nodes alias for node_count."""
        config = TopologyConfig(num_nodes=24)
        
        assert config.node_count == 24

    def test_avg_degree_alias(self):
        """Test avg_degree alias for min_degree."""
        config = TopologyConfig(avg_degree=10)
        
        assert config.min_degree == 10

    def test_rewire_probability_alias(self):
        """Test rewire_probability alias for rewiring_probability."""
        config = TopologyConfig(rewire_probability=0.75)
        
        assert config.rewiring_probability == 0.75

    def test_all_aliases_together(self):
        """Test using all aliases together."""
        config = TopologyConfig(
            num_nodes=20,
            avg_degree=6,
            rewire_probability=0.65,
        )
        
        assert config.node_count == 20
        assert config.min_degree == 6
        assert config.rewiring_probability == 0.65


class TestNodeState:
    """Test NodeState enum."""

    def test_all_states_exist(self):
        """Test all node states."""
        assert NodeState.INITIALIZING.value == "initializing"
        assert NodeState.ACTIVE.value == "active"
        assert NodeState.ESGT_MODE.value == "esgt_mode"
        assert NodeState.DEGRADED.value == "degraded"
        assert NodeState.OFFLINE.value == "offline"


class TestTIGConnection:
    """Test TIGConnection dataclass."""

    def test_creation_minimal(self):
        """Test creating with minimal fields."""
        conn = TIGConnection(remote_node_id="node-002")
        
        assert conn.remote_node_id == "node-002"
        assert conn.bandwidth_bps == 10_000_000_000
        assert conn.latency_us == 1.0
        assert conn.packet_loss == 0.0
        assert conn.active is True
        assert conn.weight == 1.0

    def test_creation_custom(self):
        """Test creating with custom values."""
        conn = TIGConnection(
            remote_node_id="node-003",
            bandwidth_bps=5_000_000_000,
            latency_us=2.5,
            packet_loss=0.01,
            active=False,
            weight=0.8,
        )
        
        assert conn.bandwidth_bps == 5_000_000_000
        assert conn.latency_us == 2.5
        assert conn.packet_loss == 0.01
        assert conn.active is False
        assert conn.weight == 0.8

    def test_get_effective_capacity_perfect(self):
        """Test effective capacity with perfect connection."""
        conn = TIGConnection(
            remote_node_id="node-004",
            bandwidth_bps=10_000_000_000,
            latency_us=1.0,
            packet_loss=0.0,
            weight=1.0,
        )
        
        capacity = conn.get_effective_capacity()
        assert capacity > 0

    def test_get_effective_capacity_inactive(self):
        """Test effective capacity of inactive connection."""
        conn = TIGConnection(
            remote_node_id="node-005",
            active=False,
        )
        
        capacity = conn.get_effective_capacity()
        assert capacity == 0.0

    def test_get_effective_capacity_with_loss(self):
        """Test effective capacity with packet loss."""
        conn = TIGConnection(
            remote_node_id="node-006",
            bandwidth_bps=10_000_000_000,
            packet_loss=0.1,  # 10% loss
        )
        
        capacity = conn.get_effective_capacity()
        assert capacity < 10_000_000_000
        assert capacity > 0

    def test_get_effective_capacity_with_latency(self):
        """Test effective capacity with high latency."""
        conn = TIGConnection(
            remote_node_id="node-007",
            bandwidth_bps=10_000_000_000,
            latency_us=100.0,  # High latency
        )
        
        capacity = conn.get_effective_capacity()
        assert capacity < 10_000_000_000

    def test_get_effective_capacity_with_weight(self):
        """Test effective capacity with reduced weight."""
        conn = TIGConnection(
            remote_node_id="node-008",
            bandwidth_bps=10_000_000_000,
            weight=0.5,  # Half weight
        )
        
        capacity = conn.get_effective_capacity()
        assert capacity < 10_000_000_000


class TestNodeHealth:
    """Test NodeHealth dataclass."""

    def test_creation_defaults(self):
        """Test creating with defaults."""
        health = NodeHealth(node_id="node-001")
        
        assert health.node_id == "node-001"
        assert health.failures == 0
        assert health.isolated is False
        assert health.degraded is False

    def test_creation_custom(self):
        """Test creating with custom values."""
        ts = time.time()
        health = NodeHealth(
            node_id="node-002",
            last_seen=ts,
            failures=2,
            isolated=True,
            degraded=False,
        )
        
        assert health.last_seen == ts
        assert health.failures == 2
        assert health.isolated is True

    def test_is_healthy_true(self):
        """Test healthy node."""
        health = NodeHealth(
            node_id="node-003",
            failures=0,
            isolated=False,
            degraded=False,
        )
        
        assert health.is_healthy() is True

    def test_is_healthy_false_isolated(self):
        """Test unhealthy due to isolation."""
        health = NodeHealth(
            node_id="node-004",
            isolated=True,
        )
        
        assert health.is_healthy() is False

    def test_is_healthy_false_degraded(self):
        """Test unhealthy due to degradation."""
        health = NodeHealth(
            node_id="node-005",
            degraded=True,
        )
        
        assert health.is_healthy() is False

    def test_is_healthy_false_too_many_failures(self):
        """Test unhealthy due to failures."""
        health = NodeHealth(
            node_id="node-006",
            failures=3,
        )
        
        assert health.is_healthy() is False

    def test_is_healthy_with_some_failures(self):
        """Test still healthy with few failures."""
        health = NodeHealth(
            node_id="node-007",
            failures=2,
        )
        
        assert health.is_healthy() is True


class TestCircuitBreaker:
    """Test CircuitBreaker class."""

    def test_creation_defaults(self):
        """Test creating with defaults."""
        breaker = CircuitBreaker()
        
        assert breaker.failure_threshold == 3
        assert breaker.recovery_timeout == 30.0
        assert breaker.state == "closed"
        assert breaker.failures == 0

    def test_creation_custom(self):
        """Test creating with custom values."""
        breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60.0,
        )
        
        assert breaker.failure_threshold == 5
        assert breaker.recovery_timeout == 60.0

    def test_is_open_initially_false(self):
        """Test circuit breaker initially closed."""
        breaker = CircuitBreaker()
        
        assert breaker.is_open() is False

    def test_record_failure_increments(self):
        """Test recording failures."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        breaker.record_failure()
        assert breaker.failures == 1
        assert breaker.state == "closed"

    def test_record_failure_opens_at_threshold(self):
        """Test circuit opens at threshold."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_failure()
        
        assert breaker.state == "open"
        assert breaker.is_open() is True

    def test_open_method(self):
        """Test manually opening circuit."""
        breaker = CircuitBreaker()
        
        breaker.open()
        
        assert breaker.state == "open"
        assert breaker.is_open() is True

    def test_is_open_transitions_to_half_open(self):
        """Test transition from open to half-open after timeout."""
        breaker = CircuitBreaker(recovery_timeout=0.1, failure_threshold=1)

        # Record failure to set last_failure_time and open the circuit
        breaker.record_failure()
        assert breaker.is_open() is True

        time.sleep(0.15)

        # Should transition to half-open
        assert breaker.is_open() is False
        assert breaker.state == "half_open"

    def test_record_success_closes_from_half_open(self):
        """Test success closes breaker from half-open."""
        breaker = CircuitBreaker()
        breaker.state = "half_open"
        
        breaker.record_success()
        
        assert breaker.state == "closed"
        assert breaker.failures == 0

    def test_record_success_no_effect_when_closed(self):
        """Test success has no effect when already closed."""
        breaker = CircuitBreaker()
        breaker.failures = 1
        
        breaker.record_success()
        
        # Should not reset failures if not in half-open
        assert breaker.failures == 1

    def test_repr(self):
        """Test string representation."""
        breaker = CircuitBreaker()
        breaker.failures = 2
        
        repr_str = repr(breaker)
        
        assert "CircuitBreaker" in repr_str
        assert "closed" in repr_str
        assert "2" in repr_str


class TestProcessingState:
    """Test ProcessingState dataclass."""

    def test_creation_defaults(self):
        """Test creating with defaults."""
        state = ProcessingState()
        
        assert state.active_modules == []
        assert state.attention_level == 0.5
        assert state.cpu_utilization == 0.0
        assert state.memory_utilization == 0.0
        assert state.phase_sync == complex(1.0, 0.0)
        assert state.processing_content is None

    def test_creation_custom(self):
        """Test creating with custom values."""
        modules = ["vision", "language"]
        content = {"task": "analysis"}
        
        state = ProcessingState(
            active_modules=modules,
            attention_level=0.8,
            cpu_utilization=75.0,
            memory_utilization=60.0,
            phase_sync=complex(0.7, 0.7),
            processing_content=content,
        )
        
        assert state.active_modules == modules
        assert state.attention_level == 0.8
        assert state.cpu_utilization == 75.0
        assert state.memory_utilization == 60.0
        assert state.phase_sync == complex(0.7, 0.7)
        assert state.processing_content == content

    def test_phase_sync_complex_number(self):
        """Test phase sync as complex number."""
        state = ProcessingState(phase_sync=complex(0.6, 0.8))
        
        assert isinstance(state.phase_sync, complex)
        assert abs(state.phase_sync - complex(0.6, 0.8)) < 0.01
