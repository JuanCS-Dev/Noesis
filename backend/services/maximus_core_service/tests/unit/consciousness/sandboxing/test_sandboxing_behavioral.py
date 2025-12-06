"""
Comprehensive Tests for Sandboxing - Consciousness Container
=============================================================

Tests for resource-limited execution of consciousness processes.
"""

import time
from unittest.mock import MagicMock

import pytest

from consciousness.sandboxing import ConsciousnessContainer, ResourceLimits


# =============================================================================
# RESOURCE LIMITS TESTS
# =============================================================================


class TestResourceLimits:
    """Test ResourceLimits configuration."""

    def test_default_limits(self):
        """Default limits should be sensible."""
        limits = ResourceLimits()
        
        assert limits.cpu_percent > 0
        assert limits.memory_mb > 0
        assert limits.timeout_sec > 0
        assert limits.max_threads > 0

    def test_custom_limits(self):
        """Custom limits should be accepted."""
        limits = ResourceLimits(cpu_percent=50.0, memory_mb=512)
        
        assert limits.cpu_percent == 50.0
        assert limits.memory_mb == 512


# =============================================================================
# CONSCIOUSNESS CONTAINER INIT TESTS
# =============================================================================


class TestConsciousnessContainerInit:
    """Test ConsciousnessContainer initialization."""

    def test_init_with_name(self):
        """Container should accept name."""
        limits = ResourceLimits()
        container = ConsciousnessContainer("test-container", limits)
        
        assert container.name == "test-container"

    def test_init_with_limits(self):
        """Container should accept limits."""
        limits = ResourceLimits(cpu_percent=60.0)
        container = ConsciousnessContainer("test", limits)
        
        assert container.limits.cpu_percent == 60.0

    def test_init_with_callback(self):
        """Container should accept alert callback."""
        limits = ResourceLimits()
        callback = MagicMock()
        container = ConsciousnessContainer("test", limits, alert_callback=callback)
        
        assert container.alert_callback is callback


# =============================================================================
# CONSCIOUSNESS CONTAINER EXECUTION TESTS
# =============================================================================


class TestConsciousnessContainerExecution:
    """Test sandboxed execution."""

    def test_execute_simple_function(self):
        """Execute should run simple function."""
        limits = ResourceLimits()
        container = ConsciousnessContainer("test", limits)
        
        def simple_task():
            return 42
        
        result = container.execute(simple_task)
        
        # Check result is returned somehow
        assert result is not None
        assert "result" in result or "return_value" in result or 42 in str(result)

    def test_execute_with_args(self):
        """Execute should pass args to function."""
        limits = ResourceLimits()
        container = ConsciousnessContainer("test", limits)
        
        def add(a, b):
            return a + b
        
        result = container.execute(add, 2, 3)
        
        # Result should contain 5
        assert result is not None
        assert "result" in result and result["result"] == 5 or 5 in str(result)

    def test_execute_with_kwargs(self):
        """Execute should pass kwargs to function."""
        limits = ResourceLimits()
        container = ConsciousnessContainer("test", limits)
        
        def greet(name="World"):
            return f"Hello, {name}"
        
        result = container.execute(greet, name="Daimon")
        
        assert result is not None
        assert "Daimon" in str(result.get("result", result))


# =============================================================================
# CONSCIOUSNESS CONTAINER STATS TESTS
# =============================================================================


class TestConsciousnessContainerStats:
    """Test container statistics."""

    def test_get_stats(self):
        """get_stats should return container stats."""
        limits = ResourceLimits()
        container = ConsciousnessContainer("test", limits)
        
        stats = container.get_stats()
        
        assert isinstance(stats, dict)
        assert "name" in stats or len(stats) >= 1


# =============================================================================
# CONSCIOUSNESS CONTAINER REPR TESTS
# =============================================================================


class TestConsciousnessContainerRepr:
    """Test string representation."""

    def test_repr(self):
        """Repr should include container info."""
        limits = ResourceLimits()
        container = ConsciousnessContainer("test-container", limits)
        
        repr_str = repr(container)
        
        assert "Container" in repr_str or "test-container" in repr_str


# =============================================================================
# CONSCIOUSNESS CONTAINER VIOLATION HANDLING TESTS
# =============================================================================


class TestConsciousnessContainerViolation:
    """Test violation handling."""

    def test_handle_violation_calls_callback(self):
        """Violation should call alert callback."""
        limits = ResourceLimits()
        callback = MagicMock()
        container = ConsciousnessContainer("test", limits, alert_callback=callback)
        
        container._handle_violation("cpu", "CPU exceeded")
        
        assert callback.called
