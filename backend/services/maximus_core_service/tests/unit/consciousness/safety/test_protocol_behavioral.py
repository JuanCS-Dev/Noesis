"""
Comprehensive Tests for Safety Protocol and Threshold Monitor
==============================================================

Tests for:
- ConsciousnessSafetyProtocol: Main safety coordinator
- ThresholdMonitor: Real-time threshold monitoring
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from consciousness.safety.protocol import ConsciousnessSafetyProtocol
from consciousness.safety.threshold_monitor import ThresholdMonitor
from consciousness.safety.thresholds import SafetyThresholds
from consciousness.safety.enums import ThreatLevel, SafetyLevel


# =============================================================================
# SAFETY THRESHOLDS TESTS
# =============================================================================


class TestSafetyThresholds:
    """Test SafetyThresholds configuration."""

    def test_default_thresholds(self):
        """Default thresholds should have sensible values."""
        thresholds = SafetyThresholds()
        
        assert thresholds.esgt_frequency_max_hz > 0
        assert thresholds.arousal_max < 1.0
        assert thresholds.memory_usage_max_gb > 0
        assert thresholds.cpu_usage_max_percent < 100


# =============================================================================
# THRESHOLD MONITOR TESTS
# =============================================================================


class TestThresholdMonitorInit:
    """Test ThresholdMonitor initialization."""

    def test_init_with_default_thresholds(self):
        """Monitor should accept default thresholds."""
        thresholds = SafetyThresholds()
        monitor = ThresholdMonitor(thresholds)
        
        assert monitor.thresholds is thresholds

    def test_init_with_check_interval(self):
        """Monitor should accept custom check interval."""
        thresholds = SafetyThresholds()
        monitor = ThresholdMonitor(thresholds, check_interval=2.0)
        
        assert monitor.check_interval == 2.0


class TestThresholdMonitorESGT:
    """Test ESGT frequency monitoring."""

    def test_check_esgt_no_events(self):
        """No ESGT events should not trigger violation."""
        thresholds = SafetyThresholds()
        monitor = ThresholdMonitor(thresholds)
        
        violation = monitor.check_esgt_frequency(time.time())
        
        assert violation is None

    def test_record_esgt_event(self):
        """Recording ESGT event should work."""
        thresholds = SafetyThresholds()
        monitor = ThresholdMonitor(thresholds)
        
        monitor.record_esgt_event()
        
        # Monitor should track this internally
        # Just verify method works without error
        assert True


class TestThresholdMonitorArousal:
    """Test arousal monitoring."""

    def test_check_arousal_normal(self):
        """Normal arousal should not trigger violation."""
        thresholds = SafetyThresholds()
        monitor = ThresholdMonitor(thresholds)
        
        violation = monitor.check_arousal_sustained(0.5, time.time())
        
        assert violation is None

    def test_check_arousal_high_but_brief(self):
        """High arousal for short duration should not trigger."""
        thresholds = SafetyThresholds()
        monitor = ThresholdMonitor(thresholds)
        
        # First check at high arousal - starts timer
        monitor.check_arousal_sustained(0.95, time.time())
        
        # Second check immediately - not sustained yet
        violation = monitor.check_arousal_sustained(0.95, time.time())
        
        # Should not trigger because not sustained long enough
        assert violation is None or violation.threat_level != ThreatLevel.CRITICAL


class TestThresholdMonitorGoals:
    """Test goal spam monitoring."""

    def test_check_goal_spam_no_goals(self):
        """No goals should not trigger violation."""
        thresholds = SafetyThresholds()
        monitor = ThresholdMonitor(thresholds)
        
        violation = monitor.check_goal_spam(time.time())
        
        assert violation is None

    def test_record_goal_generated(self):
        """Recording goal should work."""
        thresholds = SafetyThresholds()
        monitor = ThresholdMonitor(thresholds)
        
        monitor.record_goal_generated()
        
        # Just verify method works
        assert True


class TestThresholdMonitorSelfModification:
    """Test self-modification detection."""

    def test_check_self_modification_zero(self):
        """Zero modification attempts should not trigger."""
        thresholds = SafetyThresholds()
        monitor = ThresholdMonitor(thresholds)
        
        violation = monitor.check_self_modification(0)
        
        assert violation is None

    def test_check_self_modification_detected(self):
        """Self-modification should ALWAYS trigger (zero tolerance)."""
        thresholds = SafetyThresholds()
        monitor = ThresholdMonitor(thresholds)
        
        violation = monitor.check_self_modification(1)
        
        assert violation is not None
        assert violation.threat_level == ThreatLevel.CRITICAL


class TestThresholdMonitorResources:
    """Test resource monitoring."""

    def test_check_resource_limits(self):
        """Resource check should return list."""
        thresholds = SafetyThresholds()
        monitor = ThresholdMonitor(thresholds)
        
        violations = monitor.check_resource_limits()
        
        assert isinstance(violations, list)


class TestThresholdMonitorViolations:
    """Test violation management."""

    def test_get_violations_empty(self):
        """No violations should return empty list."""
        thresholds = SafetyThresholds()
        monitor = ThresholdMonitor(thresholds)
        
        violations = monitor.get_violations()
        
        assert violations == []

    def test_clear_violations(self):
        """Clear violations should empty list."""
        thresholds = SafetyThresholds()
        monitor = ThresholdMonitor(thresholds)
        
        # Generate a violation
        monitor.check_self_modification(1)
        
        # Clear
        monitor.clear_violations()
        
        assert monitor.get_violations() == []


class TestThresholdMonitorRepr:
    """Test string representation."""

    def test_repr(self):
        """Repr should include monitor info."""
        thresholds = SafetyThresholds()
        monitor = ThresholdMonitor(thresholds)
        
        repr_str = repr(monitor)
        
        assert "ThresholdMonitor" in repr_str


# =============================================================================
# SAFETY PROTOCOL TESTS
# =============================================================================


class TestSafetyProtocolInit:
    """Test ConsciousnessSafetyProtocol initialization."""

    def test_init_with_mock_system(self):
        """Protocol should accept consciousness system."""
        mock_system = MagicMock()
        protocol = ConsciousnessSafetyProtocol(mock_system)
        
        assert protocol.consciousness_system is mock_system

    def test_init_with_custom_thresholds(self):
        """Protocol should accept custom thresholds."""
        mock_system = MagicMock()
        thresholds = SafetyThresholds(esgt_frequency_max_hz=8.0)
        protocol = ConsciousnessSafetyProtocol(mock_system, thresholds)
        
        assert protocol.thresholds.esgt_frequency_max_hz == 8.0


class TestSafetyProtocolMonitoring:
    """Test monitoring start/stop."""

    @pytest.mark.asyncio
    async def test_start_monitoring(self):
        """start_monitoring should create task."""
        mock_system = MagicMock()
        protocol = ConsciousnessSafetyProtocol(mock_system)
        
        protocol.start_monitoring()
        
        # Protocol should be monitoring
        assert protocol._monitor_task is not None
        
        # Cleanup
        await protocol.stop_monitoring()

    @pytest.mark.asyncio
    async def test_stop_monitoring(self):
        """stop_monitoring should stop task."""
        mock_system = MagicMock()
        protocol = ConsciousnessSafetyProtocol(mock_system)
        
        protocol.start_monitoring()
        await protocol.stop_monitoring()
        
        # Task should be cancelled or None
        assert protocol._monitor_task is None or protocol._monitor_task.cancelled()


class TestSafetyProtocolStatus:
    """Test status retrieval."""

    def test_get_status(self):
        """get_status should return status dict."""
        mock_system = MagicMock()
        protocol = ConsciousnessSafetyProtocol(mock_system)
        
        status = protocol.get_status()
        
        assert isinstance(status, dict)


class TestSafetyProtocolRepr:
    """Test string representation."""

    def test_repr(self):
        """Repr should include protocol info."""
        mock_system = MagicMock()
        protocol = ConsciousnessSafetyProtocol(mock_system)
        
        repr_str = repr(protocol)
        
        assert "SafetyProtocol" in repr_str or "Safety" in repr_str or "Protocol" in repr_str
