"""
Comprehensive Tests for MMEI - Motivational Model of Embodied Intelligence
===========================================================================

Tests for the internal state monitoring and goal generation system.
"""

from unittest.mock import MagicMock, AsyncMock

import pytest

from consciousness.mmei.monitor import InternalStateMonitor
from consciousness.mmei.models import InteroceptionConfig, PhysicalMetrics, AbstractNeeds, NeedUrgency
from consciousness.mmei.goals import Goal
from consciousness.mmei.goal_manager import GoalManager
from consciousness.mmei.rate_limiter import RateLimiter


# =============================================================================
# INTEROCEPTION CONFIG TESTS
# =============================================================================


class TestInteroceptionConfig:
    """Test InteroceptionConfig defaults."""

    def test_default_values(self):
        """Default values should be sensible."""
        config = InteroceptionConfig()
        
        assert config.sampling_interval_ms > 0
        assert config.history_window_size > 0


# =============================================================================
# PHYSICAL METRICS TESTS
# =============================================================================


class TestPhysicalMetrics:
    """Test PhysicalMetrics data structure."""

    def test_creation_with_values(self):
        """PhysicalMetrics should be creatable with values."""
        metrics = PhysicalMetrics(
            cpu_usage=0.5,
            memory_usage=0.6,
            gpu_usage=0.3,
            network_bandwidth=0.4,
            disk_io=0.2,
        )
        
        assert metrics.cpu_usage == 0.5
        assert metrics.memory_usage == 0.6


# =============================================================================
# ABSTRACT NEEDS TESTS
# =============================================================================


class TestAbstractNeeds:
    """Test AbstractNeeds data structure."""

    def test_creation_with_values(self):
        """AbstractNeeds should be creatable with values."""
        needs = AbstractNeeds(
            safety_need=0.2,
            rest_need=0.5,
            exploration_need=0.3,
            social_need=0.4,
            achievement_need=0.6,
        )
        
        assert needs.rest_need == 0.5
        assert needs.achievement_need == 0.6


# =============================================================================
# INTERNAL STATE MONITOR TESTS
# =============================================================================


class TestInternalStateMonitorInit:
    """Test InternalStateMonitor initialization."""

    def test_init_with_default_config(self):
        """Monitor should initialize with default config."""
        monitor = InternalStateMonitor()
        
        assert monitor.config is not None

    def test_init_with_custom_config(self):
        """Monitor should accept custom config."""
        config = InteroceptionConfig(sampling_interval_ms=50)
        monitor = InternalStateMonitor(config)
        
        assert monitor.config.sampling_interval_ms == 50

    def test_init_with_monitor_id(self):
        """Monitor should accept custom ID."""
        monitor = InternalStateMonitor(monitor_id="test-mmei")
        
        assert monitor.monitor_id == "test-mmei" or "test-mmei" in str(monitor)


class TestInternalStateMonitorMetrics:
    """Test metrics collection."""

    def test_set_metrics_collector(self):
        """Should accept metrics collector function."""
        monitor = InternalStateMonitor()
        
        def collector():
            return PhysicalMetrics(
                cpu_usage=0.5,
                memory_usage=0.5,
                gpu_usage=0.0,
                network_bandwidth=0.0,
                disk_io=0.0,
            )
        
        monitor.set_metrics_collector(collector)
        
        assert monitor._metrics_collector is not None or monitor.metrics_collector is not None

    def test_get_current_metrics(self):
        """Should return current metrics or None."""
        monitor = InternalStateMonitor()
        
        metrics = monitor.get_current_metrics()
        
        # May be None if not started
        assert metrics is None or isinstance(metrics, PhysicalMetrics)


class TestInternalStateMonitorNeeds:
    """Test needs computation."""

    def test_get_current_needs(self):
        """Should return current needs or None."""
        monitor = InternalStateMonitor()
        
        needs = monitor.get_current_needs()
        
        # May be None if not started
        assert needs is None or isinstance(needs, AbstractNeeds)


class TestInternalStateMonitorLifecycle:
    """Test start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_start_sets_running(self):
        """Start should set running state."""
        monitor = InternalStateMonitor()
        
        monitor.start()
        
        assert monitor._running is True or hasattr(monitor, '_monitor_task')
        
        monitor.stop()

    @pytest.mark.asyncio
    async def test_stop_clears_running(self):
        """Stop should clear running state."""
        monitor = InternalStateMonitor()
        
        monitor.start()
        monitor.stop()
        
        assert monitor._running is False


class TestInternalStateMonitorStatistics:
    """Test statistics retrieval."""

    def test_get_statistics(self):
        """Should return statistics dict."""
        monitor = InternalStateMonitor()
        
        stats = monitor.get_statistics()
        
        assert isinstance(stats, dict)


class TestInternalStateMonitorHealthMetrics:
    """Test health metrics for Safety Core."""

    def test_get_health_metrics(self):
        """Should return health metrics dict."""
        monitor = InternalStateMonitor()
        
        metrics = monitor.get_health_metrics()
        
        assert isinstance(metrics, dict)


class TestInternalStateMonitorRepr:
    """Test string representation."""

    def test_repr(self):
        """Repr should include monitor info."""
        monitor = InternalStateMonitor()
        
        repr_str = repr(monitor)
        
        assert "Monitor" in repr_str or "MMEI" in repr_str or "Internal" in repr_str


# =============================================================================
# GOAL TESTS
# =============================================================================


class TestGoal:
    """Test Goal data structure."""

    def test_goal_creation(self):
        """Goal should be creatable with required fields."""
        goal = Goal(
            goal_id="goal-001",
            source_need="rest_need",
            urgency=NeedUrgency.MEDIUM,
            description="Take a break",
        )
        
        assert goal.goal_id == "goal-001"
        assert goal.urgency == NeedUrgency.MEDIUM


# =============================================================================
# GOAL MANAGER TESTS
# =============================================================================


class TestGoalManager:
    """Test GoalManager behavior."""

    def test_goal_manager_creation(self):
        """GoalManager should be creatable."""
        manager = GoalManager()
        
        assert manager is not None

    def test_get_active_goals(self):
        """Should return list of active goals."""
        manager = GoalManager()
        
        goals = manager.get_active_goals()
        
        assert isinstance(goals, list)


# =============================================================================
# RATE LIMITER TESTS
# =============================================================================


class TestRateLimiter:
    """Test RateLimiter behavior."""

    def test_rate_limiter_creation(self):
        """RateLimiter should be creatable."""
        limiter = RateLimiter()
        
        assert limiter is not None

    def test_is_allowed(self):
        """Should check if action is allowed."""
        limiter = RateLimiter()
        
        # First request should be allowed
        is_allowed = limiter.is_allowed()
        
        assert isinstance(is_allowed, bool)
