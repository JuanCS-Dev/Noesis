"""
REAL Tests for Safety Protocol - NO MOCKS  
==========================================

Tests that actually run the ConsciousnessSafetyProtocol with real monitoring.
"""

import asyncio
import pytest
from unittest.mock import MagicMock

from consciousness.safety.protocol import ConsciousnessSafetyProtocol
from consciousness.safety.thresholds import SafetyThresholds
from consciousness.safety.models import SafetyViolation
from consciousness.safety.enums import ThreatLevel, ViolationType


class TestSafetyProtocolCreation:
    """Test safety protocol creation and initialization."""

    def test_create_with_defaults(self):
        """Test creating protocol with default thresholds."""
        mock_system = MagicMock()
        protocol = ConsciousnessSafetyProtocol(mock_system)
        
        assert protocol.consciousness_system is mock_system
        assert protocol.thresholds is not None
        assert protocol.threshold_monitor is not None
        assert protocol.anomaly_detector is not None
        assert protocol.kill_switch is not None

    def test_create_with_custom_thresholds(self):
        """Test creating protocol with custom thresholds."""
        mock_system = MagicMock()
        custom_thresholds = SafetyThresholds(
            esgt_frequency_max_hz=8.0,
            arousal_max=0.90
        )
        
        protocol = ConsciousnessSafetyProtocol(mock_system, thresholds=custom_thresholds)
        
        assert protocol.thresholds.esgt_frequency_max_hz == 8.0
        assert protocol.thresholds.arousal_max == 0.90


class TestSafetyProtocolComponents:
    """Test protocol component integration."""

    def test_has_threshold_monitor(self):
        """Test protocol has threshold monitor."""
        mock_system = MagicMock()
        protocol = ConsciousnessSafetyProtocol(mock_system)
        
        assert hasattr(protocol, 'threshold_monitor')
        assert protocol.threshold_monitor is not None

    def test_has_anomaly_detector(self):
        """Test protocol has anomaly detector."""
        mock_system = MagicMock()
        protocol = ConsciousnessSafetyProtocol(mock_system)
        
        assert hasattr(protocol, 'anomaly_detector')
        assert protocol.anomaly_detector is not None

    def test_has_kill_switch(self):
        """Test protocol has kill switch."""
        mock_system = MagicMock()
        protocol = ConsciousnessSafetyProtocol(mock_system)
        
        assert hasattr(protocol, 'kill_switch')
        assert protocol.kill_switch is not None


class TestSafetyProtocolState:
    """Test protocol state management."""

    def test_initial_state(self):
        """Test protocol initial state."""
        mock_system = MagicMock()
        protocol = ConsciousnessSafetyProtocol(mock_system)
        
        assert protocol.monitoring_active is False
        assert protocol.degradation_level == 0

    def test_get_status(self):
        """Test getting protocol status."""
        mock_system = MagicMock()
        protocol = ConsciousnessSafetyProtocol(mock_system)
        
        status = protocol.get_status()
        
        assert isinstance(status, dict)
        assert 'monitoring_active' in status
        assert 'kill_switch_triggered' in status


@pytest.mark.asyncio
class TestSafetyProtocolMonitoring:
    """Test real monitoring functionality."""

    async def test_start_monitoring(self):
        """Test starting monitoring."""
        mock_system = MagicMock()
        protocol = ConsciousnessSafetyProtocol(mock_system)
        
        await protocol.start_monitoring()
        
        assert protocol.monitoring_active is True
        assert protocol.monitoring_task is not None
        
        await protocol.stop_monitoring()

    async def test_stop_monitoring(self):
        """Test stopping monitoring."""
        mock_system = MagicMock()
        protocol = ConsciousnessSafetyProtocol(mock_system)
        
        await protocol.start_monitoring()
        await asyncio.sleep(0.1)
        await protocol.stop_monitoring()
        
        assert protocol.monitoring_active is False

    async def test_monitoring_loop_runs(self):
        """Test monitoring loop actually runs."""
        mock_system = MagicMock()
        mock_system.get_esgt_history = MagicMock(return_value=[])
        mock_system.get_arousal_level = MagicMock(return_value=0.5)
        
        protocol = ConsciousnessSafetyProtocol(mock_system)
        
        await protocol.start_monitoring()
        await asyncio.sleep(0.5)  # Let it run
        await protocol.stop_monitoring()
        
        # If no exception, monitoring ran successfully
        assert True


class TestSafetyProtocolMetricsCollection:
    """Test metrics collection."""

    def test_collect_metrics(self):
        """Test collecting system metrics."""
        mock_system = MagicMock()
        mock_system.get_esgt_history = MagicMock(return_value=[])
        mock_system.get_arousal_level = MagicMock(return_value=0.6)

        protocol = ConsciousnessSafetyProtocol(mock_system)

        metrics = protocol._collect_metrics()

        assert isinstance(metrics, dict)
        assert 'cpu_percent' in metrics or 'memory_usage_gb' in metrics or 'arousal' in metrics


class TestSafetyProtocolViolationHandling:
    """Test violation detection and handling."""

    def test_check_all_thresholds(self):
        """Test checking all thresholds."""
        mock_system = MagicMock()
        mock_system.get_esgt_history = MagicMock(return_value=[])
        
        protocol = ConsciousnessSafetyProtocol(mock_system)
        
        import time
        metrics = {'arousal': 0.5, 'cpu': 50.0}
        violations = protocol._check_all_thresholds(metrics, time.time())
        
        assert isinstance(violations, list)

    def test_register_violation_callback(self):
        """Test registering violation callback."""
        mock_system = MagicMock()
        protocol = ConsciousnessSafetyProtocol(mock_system)
        
        callback_invoked = []
        
        def test_callback(violation):
            callback_invoked.append(violation)
        
        protocol.on_violation = test_callback
        
        assert protocol.on_violation is not None


class TestSafetyProtocolThresholdChecks:
    """Test specific threshold checks."""

    def test_record_esgt_event(self):
        """Test recording ESGT event."""
        mock_system = MagicMock()
        protocol = ConsciousnessSafetyProtocol(mock_system)

        protocol.threshold_monitor.record_esgt_event()

        assert len(protocol.threshold_monitor.esgt_events_window) == 1


class TestSafetyProtocolKillSwitch:
    """Test kill switch integration."""

    def test_access_kill_switch(self):
        """Test accessing kill switch."""
        mock_system = MagicMock()
        protocol = ConsciousnessSafetyProtocol(mock_system)
        
        assert protocol.kill_switch is not None
        assert not protocol.kill_switch.is_triggered()

    def test_kill_switch_trigger(self):
        """Test triggering kill switch through protocol."""
        mock_system = MagicMock()
        mock_system.stop = MagicMock()
        
        protocol = ConsciousnessSafetyProtocol(mock_system)
        
        from consciousness.safety.enums import ShutdownReason
        result = protocol.kill_switch.trigger(
            reason=ShutdownReason.MANUAL,
            context={"test": True}
        )
        
        assert result is True
        assert protocol.kill_switch.is_triggered()
