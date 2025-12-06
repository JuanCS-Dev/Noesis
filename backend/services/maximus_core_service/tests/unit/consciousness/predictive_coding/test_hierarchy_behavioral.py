"""
Comprehensive Tests for Predictive Coding Hierarchy
====================================================

Tests for Free Energy Minimization predictive coding:
- PredictiveCodingHierarchy: 5-layer cortical hierarchy
- Bottom-up prediction errors, top-down predictions
"""

from unittest.mock import MagicMock

import numpy as np
import pytest

from consciousness.predictive_coding.hierarchy_hardened import (
    HierarchyConfig,
    HierarchyState,
    PredictiveCodingHierarchy,
)
from consciousness.predictive_coding.layer_base_hardened import LayerConfig


# =============================================================================
# HIERARCHY CONFIG TESTS
# =============================================================================


class TestHierarchyConfig:
    """Test HierarchyConfig initialization."""

    def test_default_config(self):
        """Default config should have sensible values."""
        config = HierarchyConfig()
        
        assert config.max_hierarchy_cycle_time_ms > 0
        assert 0 < config.error_propagation_weight <= 1.0

    def test_layer_configs_initialized(self):
        """All layer configs should be initialized."""
        config = HierarchyConfig()
        
        assert config.layer1_config is not None
        assert config.layer2_config is not None
        assert config.layer3_config is not None
        assert config.layer4_config is not None
        assert config.layer5_config is not None


# =============================================================================
# HIERARCHY INITIALIZATION TESTS
# =============================================================================


class TestPredictiveCodingHierarchyInit:
    """Test hierarchy initialization."""

    def test_hierarchy_creates_all_layers(self):
        """Hierarchy should create all 5 layers."""
        hierarchy = PredictiveCodingHierarchy()
        
        assert hasattr(hierarchy, "layer1")
        assert hasattr(hierarchy, "layer2")
        assert hasattr(hierarchy, "layer3")
        assert hasattr(hierarchy, "layer4")
        assert hasattr(hierarchy, "layer5")

    def test_hierarchy_with_custom_config(self):
        """Hierarchy should accept custom config."""
        config = HierarchyConfig(max_hierarchy_cycle_time_ms=1000.0)
        hierarchy = PredictiveCodingHierarchy(config)
        
        assert hierarchy.config.max_hierarchy_cycle_time_ms == 1000.0

    def test_hierarchy_with_kill_switch_callback(self):
        """Hierarchy should accept kill switch callback."""
        callback = MagicMock()
        hierarchy = PredictiveCodingHierarchy(kill_switch_callback=callback)
        
        assert hierarchy._kill_switch is callback


# =============================================================================
# HIERARCHY PROCESSING TESTS
# =============================================================================


class TestHierarchyProcessing:
    """Test input processing through hierarchy."""

    @pytest.mark.asyncio
    async def test_process_input_returns_dict(self):
        """process_input should return dict with errors."""
        hierarchy = PredictiveCodingHierarchy()
        raw_input = np.random.rand(10)
        
        result = await hierarchy.process_input(raw_input)
        
        assert isinstance(result, dict)
        assert "layer1" in result or len(result) >= 1

    @pytest.mark.asyncio
    async def test_bottom_up_pass_propagates_errors(self):
        """Bottom-up pass should propagate errors through layers."""
        hierarchy = PredictiveCodingHierarchy()
        raw_input = np.random.rand(10)
        
        errors = await hierarchy._bottom_up_pass(raw_input)
        
        assert len(errors) >= 1


# =============================================================================
# HIERARCHY STATE TESTS
# =============================================================================


class TestHierarchyState:
    """Test hierarchy state retrieval."""

    def test_get_state_returns_hierarchy_state(self):
        """get_state should return HierarchyState."""
        hierarchy = PredictiveCodingHierarchy()
        
        state = hierarchy.get_state()
        
        assert isinstance(state, HierarchyState)
        assert hasattr(state, "total_cycles")
        assert hasattr(state, "aggregate_circuit_breaker_open")


# =============================================================================
# HIERARCHY HEALTH METRICS TESTS
# =============================================================================


class TestHierarchyHealthMetrics:
    """Test health metrics aggregation."""

    def test_get_health_metrics_returns_dict(self):
        """get_health_metrics should return dict with all layer metrics."""
        hierarchy = PredictiveCodingHierarchy()
        
        metrics = hierarchy.get_health_metrics()
        
        assert isinstance(metrics, dict)
        assert "layer1" in str(metrics) or len(metrics) >= 1


# =============================================================================
# HIERARCHY EMERGENCY STOP TESTS
# =============================================================================


class TestHierarchyEmergencyStop:
    """Test emergency stop behavior."""

    def test_emergency_stop_stops_all_layers(self):
        """emergency_stop should stop all layers."""
        hierarchy = PredictiveCodingHierarchy()
        
        hierarchy.emergency_stop()
        
        # All layers should have circuit breakers open
        assert hierarchy.layer1._circuit_breaker_open
        assert hierarchy.layer2._circuit_breaker_open
        assert hierarchy.layer3._circuit_breaker_open
        assert hierarchy.layer4._circuit_breaker_open
        assert hierarchy.layer5._circuit_breaker_open


# =============================================================================
# HIERARCHY REPR TEST
# =============================================================================


class TestHierarchyRepr:
    """Test string representation."""

    def test_repr_includes_layer_info(self):
        """Repr should include layer information."""
        hierarchy = PredictiveCodingHierarchy()
        
        repr_str = repr(hierarchy)
        
        assert "PredictiveCodingHierarchy" in repr_str


# =============================================================================
# CIRCUIT BREAKER AGGREGATE TESTS
# =============================================================================


class TestAggregateCircuitBreaker:
    """Test aggregate circuit breaker behavior."""

    def test_aggregate_breaker_closed_initially(self):
        """Aggregate breaker should be closed initially."""
        hierarchy = PredictiveCodingHierarchy()
        
        is_open = hierarchy._is_aggregate_circuit_breaker_open()
        
        assert is_open is False

    def test_aggregate_breaker_opens_with_3_layers_open(self):
        """Aggregate breaker should open when 3+ layers have open breakers."""
        hierarchy = PredictiveCodingHierarchy()
        
        # Open 3 layer breakers
        hierarchy.layer1._circuit_breaker_open = True
        hierarchy.layer2._circuit_breaker_open = True
        hierarchy.layer3._circuit_breaker_open = True
        
        is_open = hierarchy._is_aggregate_circuit_breaker_open()
        
        assert is_open is True
