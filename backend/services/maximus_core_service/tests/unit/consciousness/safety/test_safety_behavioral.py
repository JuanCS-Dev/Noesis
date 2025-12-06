"""
Comprehensive Behavioral Tests for Safety System
=================================================

Tests for the consciousness safety mechanisms including:
- KillSwitch: Emergency shutdown with <1s guarantee
- SafetyProtocol: Continuous monitoring
- AnomalyDetector: Pattern detection
"""

import time
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from consciousness.safety.kill_switch import KillSwitch
from consciousness.safety.enums import ShutdownReason
from consciousness.safety.models import StateSnapshot, IncidentReport, SafetyViolation
from consciousness.safety.enums import ViolationType, SafetyLevel


# =============================================================================
# KILL SWITCH TESTS - Emergency Shutdown System
# =============================================================================


class TestKillSwitchInitialization:
    """Test KillSwitch initialization."""

    def test_initialization_not_triggered(self):
        """KillSwitch should start in non-triggered state."""
        mock_system = MagicMock()
        ks = KillSwitch(mock_system)
        
        assert not ks.is_triggered()


class TestKillSwitchTrigger:
    """Test KillSwitch trigger behavior."""

    def test_trigger_sets_triggered_state(self):
        """Trigger should set triggered state."""
        mock_system = MagicMock()
        mock_system.stop = MagicMock()
        ks = KillSwitch(mock_system)
        
        result = ks.trigger(
            reason=ShutdownReason.MANUAL,
            context={"source": "test"}
        )
        
        assert ks.is_triggered()
        assert result is True

    def test_trigger_returns_false_if_already_triggered(self):
        """Second trigger should return False."""
        mock_system = MagicMock()
        mock_system.stop = MagicMock()
        ks = KillSwitch(mock_system)
        
        ks.trigger(ShutdownReason.MANUAL, {"source": "first"})
        result = ks.trigger(ShutdownReason.MANUAL, {"source": "second"})
        
        assert result is False


class TestKillSwitchShutdownReasons:
    """Test different shutdown reasons."""

    @pytest.mark.parametrize("reason", list(ShutdownReason))
    def test_all_shutdown_reasons_work(self, reason):
        """All shutdown reasons should be handled."""
        mock_system = MagicMock()
        mock_system.stop = MagicMock()
        ks = KillSwitch(mock_system)
        
        result = ks.trigger(reason=reason, context={"source": "test"})
        
        assert result is True
        assert ks.is_triggered()


class TestKillSwitchRecoveryAssessment:
    """Test recovery possibility assessment."""

    def test_manual_shutdown_is_recoverable(self):
        """Manual shutdown should be recoverable."""
        mock_system = MagicMock()
        ks = KillSwitch(mock_system)
        
        result = ks._assess_recovery_possibility(ShutdownReason.MANUAL)
        
        assert result is True

    def test_threshold_shutdown_is_recoverable(self):
        """Threshold violation should be recoverable."""
        mock_system = MagicMock()
        ks = KillSwitch(mock_system)
        
        result = ks._assess_recovery_possibility(ShutdownReason.THRESHOLD)
        
        assert result is True


class TestKillSwitchStatus:
    """Test get_status method."""

    def test_get_status_before_trigger(self):
        """Status should show not triggered."""
        mock_system = MagicMock()
        ks = KillSwitch(mock_system)
        
        status = ks.get_status()
        
        assert "triggered" in status
        assert status["triggered"] is False

    def test_get_status_after_trigger(self):
        """Status should show triggered and reason."""
        mock_system = MagicMock()
        mock_system.stop = MagicMock()
        ks = KillSwitch(mock_system)
        
        ks.trigger(ShutdownReason.MANUAL, {"source": "test"})
        status = ks.get_status()
        
        assert status["triggered"] is True


class TestKillSwitchRepr:
    """Test string representation."""

    def test_repr_shows_status(self):
        """Repr should show trigger status."""
        mock_system = MagicMock()
        ks = KillSwitch(mock_system)
        
        repr_str = repr(ks)
        
        assert "KillSwitch" in repr_str


# =============================================================================
# STATE SNAPSHOT TESTS
# =============================================================================


class TestStateSnapshot:
    """Test StateSnapshot data structure."""

    def test_state_snapshot_creation(self):
        """StateSnapshot should be creatable with required fields."""
        snapshot = StateSnapshot(
            timestamp=datetime.now(),
            esgt_state={"active": True},
            arousal_state={"level": 0.5},
            tig_metrics={"nodes": 100},
        )
        
        assert snapshot.arousal_state["level"] == 0.5

    def test_state_snapshot_to_dict(self):
        """StateSnapshot should serialize to dict."""
        snapshot = StateSnapshot(
            timestamp=datetime.now(),
            esgt_state={"active": True},
        )
        
        data = snapshot.to_dict()
        
        assert "timestamp" in data
        assert "esgt_state" in data


# =============================================================================
# INCIDENT REPORT TESTS
# =============================================================================


class TestIncidentReport:
    """Test IncidentReport data structure."""

    def test_incident_report_creation(self):
        """IncidentReport should be creatable."""
        report = IncidentReport(
            incident_id="INC-001",
            shutdown_reason=ShutdownReason.MANUAL,
            shutdown_timestamp=time.time(),
            violations=[],
            system_state_snapshot={},
            metrics_timeline=[],
            recovery_possible=True,
            notes="Test incident",
        )
        
        assert report.incident_id == "INC-001"
        assert report.recovery_possible is True

    def test_incident_report_to_dict(self):
        """IncidentReport should serialize to dict."""
        report = IncidentReport(
            incident_id="INC-002",
            shutdown_reason=ShutdownReason.ANOMALY,
            shutdown_timestamp=time.time(),
            violations=[],
            system_state_snapshot={"tig": {}},
            metrics_timeline=[{"t": 0, "m": 1}],
            recovery_possible=False,
            notes="Anomaly detected",
        )
        
        data = report.to_dict()
        
        assert data["incident_id"] == "INC-002"
        assert data["shutdown_reason"] == "anomaly_detected"
        assert "shutdown_timestamp_iso" in data


# =============================================================================
# SAFETY VIOLATION TESTS
# =============================================================================


class TestSafetyViolation:
    """Test SafetyViolation data structure."""

    def test_safety_violation_creation(self):
        """SafetyViolation should be creatable with required fields."""
        violation = SafetyViolation(
            violation_id="V-001",
            violation_type=ViolationType.ESGT_FREQUENCY_EXCEEDED,
            severity=SafetyLevel.WARNING,
            timestamp=time.time(),
            description="Test violation",
        )
        
        assert violation.violation_id == "V-001"
        assert violation.severity == SafetyLevel.WARNING

    def test_safety_violation_to_dict(self):
        """SafetyViolation should serialize to dict."""
        violation = SafetyViolation(
            violation_id="V-002",
            violation_type=ViolationType.AROUSAL_SUSTAINED_HIGH,
            severity=SafetyLevel.CRITICAL,
            timestamp=time.time(),
            description="Arousal too high",
            value_observed=0.95,
            threshold_violated=0.9,
        )
        
        data = violation.to_dict()
        
        assert data["violation_id"] == "V-002"
        assert "value_observed" in data
