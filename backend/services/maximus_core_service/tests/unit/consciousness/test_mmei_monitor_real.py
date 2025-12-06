"""
REAL Tests for MMEI Internal State Monitor - NO MOCKS
======================================================

Tests that actually run the InternalStateMonitor with real metrics collection.
"""

import asyncio
import pytest

from consciousness.mmei.monitor import InternalStateMonitor
from consciousness.mmei.models import InteroceptionConfig, PhysicalMetrics, AbstractNeeds


class TestInternalStateMonitorCreation:
    """Test monitor creation and initialization."""

    def test_create_with_defaults(self):
        """Test creating monitor with defaults."""
        monitor = InternalStateMonitor()
        
        assert monitor.monitor_id == "mmei-monitor-primary"
        assert monitor.config is not None

    def test_create_with_custom_config(self):
        """Test creating monitor with custom config."""
        config = InteroceptionConfig()
        monitor = InternalStateMonitor(config=config, monitor_id="test-monitor")
        
        assert monitor.monitor_id == "test-monitor"
        assert monitor.config is config


class TestInternalStateMonitorState:
    """Test monitor state management."""

    def test_initial_state(self):
        """Test monitor initial state."""
        monitor = InternalStateMonitor()
        
        assert monitor.total_collections == 0
        assert monitor.failed_collections == 0

    def test_get_current_needs(self):
        """Test getting current needs."""
        monitor = InternalStateMonitor()
        
        needs = monitor.get_current_needs()
        
        # Initially may be None or default needs
        assert needs is None or isinstance(needs, AbstractNeeds)


class TestInternalStateMonitorMetricsCollection:
    """Test metrics collection functionality."""

    def test_set_metrics_collector(self):
        """Test setting metrics collector."""
        monitor = InternalStateMonitor()

        def test_collector():
            return PhysicalMetrics()

        monitor.set_metrics_collector(test_collector)

        assert monitor._metrics_collector is not None

    def test_set_async_metrics_collector(self):
        """Test setting async metrics collector."""
        monitor = InternalStateMonitor()

        async def test_async_collector():
            return PhysicalMetrics()

        monitor.set_metrics_collector(test_async_collector)

        assert monitor._metrics_collector is not None


class TestInternalStateMonitorCallbacks:
    """Test need change callbacks."""

    def test_register_need_callback(self):
        """Test registering need callback."""
        monitor = InternalStateMonitor()
        
        callback_invoked = []
        
        async def test_callback(needs):
            callback_invoked.append(needs)
        
        monitor.register_need_callback(test_callback, threshold=0.7)
        
        assert len(monitor._need_callbacks) > 0


@pytest.mark.asyncio
class TestInternalStateMonitorAsyncOperations:
    """Test async monitor operations."""

    async def test_start_and_stop(self):
        """Test starting and stopping monitor."""
        monitor = InternalStateMonitor()
        
        # Set a simple collector
        def collector():
            return PhysicalMetrics()
        
        monitor.set_metrics_collector(collector)
        
        await monitor.start()
        assert monitor._running is True
        
        await asyncio.sleep(0.1)
        
        await monitor.stop()
        assert monitor._running is False

    async def test_monitor_collects_metrics(self):
        """Test monitor actually collects metrics."""
        config = InteroceptionConfig()
        monitor = InternalStateMonitor(config=config)
        
        def collector():
            return PhysicalMetrics()
        
        monitor.set_metrics_collector(collector)
        
        initial_collections = monitor.total_collections
        
        await monitor.start()
        await asyncio.sleep(0.3)  # Let it collect a few times
        await monitor.stop()
        
        assert monitor.total_collections > initial_collections


class TestInternalStateMonitorNeedsComputation:
    """Test needs computation from metrics."""

    def test_needs_computation_engine_exists(self):
        """Test monitor has needs computation engine."""
        monitor = InternalStateMonitor()
        
        assert hasattr(monitor, 'needs_computation')
        assert monitor.needs_computation is not None


class TestInternalStateMonitorGoalManagement:
    """Test goal manager integration."""

    def test_has_goal_manager(self):
        """Test monitor has goal manager."""
        monitor = InternalStateMonitor()
        
        assert hasattr(monitor, 'goal_manager')
        assert monitor.goal_manager is not None


class TestInternalStateMonitorPerformanceTracking:
    """Test performance tracking."""

    def test_tracks_collection_count(self):
        """Test monitor tracks collection count."""
        monitor = InternalStateMonitor()
        
        assert hasattr(monitor, 'total_collections')
        assert hasattr(monitor, 'failed_collections')
        assert monitor.total_collections == 0

    def test_tracks_callback_invocations(self):
        """Test monitor tracks callback invocations."""
        monitor = InternalStateMonitor()
        
        assert hasattr(monitor, 'callback_invocations')
        assert monitor.callback_invocations == 0
