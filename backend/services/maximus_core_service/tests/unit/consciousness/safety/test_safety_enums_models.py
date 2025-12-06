"""
Comprehensive tests for safety/enums.py and safety/models.py

Tests cover:
- ThreatLevel enum
- SafetyLevel enum and conversion methods
- SafetyViolationType enum
- ViolationType enum and to_modern()
- ViolationTypeAdapter
- ShutdownReason enum
- SafetyViolation data class
- IncidentReport data class
- StateSnapshot data class
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from consciousness.safety.enums import (
    SafetyLevel,
    SafetyViolationType,
    ShutdownReason,
    ThreatLevel,
    ViolationType,
    ViolationTypeAdapter,
    _LEGACY_TO_MODERN_VIOLATION,
    _MODERN_TO_LEGACY_VIOLATION,
)
from consciousness.safety.models import IncidentReport, SafetyViolation, StateSnapshot


# ==================== ENUMS TESTS ====================


class TestThreatLevel:
    """Test ThreatLevel enum."""

    def test_all_threat_levels_exist(self):
        """Test that all expected threat levels are defined."""
        assert ThreatLevel.NONE.value == "none"
        assert ThreatLevel.LOW.value == "low"
        assert ThreatLevel.MEDIUM.value == "medium"
        assert ThreatLevel.HIGH.value == "high"
        assert ThreatLevel.CRITICAL.value == "critical"

    def test_threat_level_membership(self):
        """Test threat level enum membership."""
        assert ThreatLevel.NONE in ThreatLevel
        assert ThreatLevel.LOW in ThreatLevel
        assert ThreatLevel.MEDIUM in ThreatLevel
        assert ThreatLevel.HIGH in ThreatLevel
        assert ThreatLevel.CRITICAL in ThreatLevel

    def test_threat_level_from_string(self):
        """Test creating ThreatLevel from string value."""
        assert ThreatLevel("none") == ThreatLevel.NONE
        assert ThreatLevel("low") == ThreatLevel.LOW
        assert ThreatLevel("critical") == ThreatLevel.CRITICAL


class TestSafetyLevel:
    """Test SafetyLevel enum."""

    def test_all_safety_levels_exist(self):
        """Test that all expected safety levels are defined."""
        assert SafetyLevel.NORMAL.value == "normal"
        assert SafetyLevel.WARNING.value == "warning"
        assert SafetyLevel.CRITICAL.value == "critical"
        assert SafetyLevel.EMERGENCY.value == "emergency"

    def test_from_threat_conversion(self):
        """Test conversion from ThreatLevel to SafetyLevel."""
        assert SafetyLevel.from_threat(ThreatLevel.NONE) == SafetyLevel.NORMAL
        assert SafetyLevel.from_threat(ThreatLevel.LOW) == SafetyLevel.WARNING
        assert SafetyLevel.from_threat(ThreatLevel.MEDIUM) == SafetyLevel.WARNING
        assert SafetyLevel.from_threat(ThreatLevel.HIGH) == SafetyLevel.CRITICAL
        assert SafetyLevel.from_threat(ThreatLevel.CRITICAL) == SafetyLevel.EMERGENCY

    def test_to_threat_conversion(self):
        """Test conversion from SafetyLevel to ThreatLevel."""
        assert SafetyLevel.NORMAL.to_threat() == ThreatLevel.NONE
        assert SafetyLevel.WARNING.to_threat() == ThreatLevel.LOW
        assert SafetyLevel.CRITICAL.to_threat() == ThreatLevel.HIGH
        assert SafetyLevel.EMERGENCY.to_threat() == ThreatLevel.CRITICAL

    def test_bidirectional_conversion(self):
        """Test round-trip conversion between SafetyLevel and ThreatLevel."""
        # NORMAL -> NONE -> NORMAL
        assert SafetyLevel.from_threat(SafetyLevel.NORMAL.to_threat()) == SafetyLevel.NORMAL
        # WARNING -> LOW -> WARNING
        assert SafetyLevel.from_threat(SafetyLevel.WARNING.to_threat()) == SafetyLevel.WARNING
        # CRITICAL -> HIGH -> CRITICAL
        assert SafetyLevel.from_threat(SafetyLevel.CRITICAL.to_threat()) == SafetyLevel.CRITICAL
        # EMERGENCY -> CRITICAL -> EMERGENCY
        assert SafetyLevel.from_threat(SafetyLevel.EMERGENCY.to_threat()) == SafetyLevel.EMERGENCY


class TestSafetyViolationType:
    """Test SafetyViolationType enum."""

    def test_all_violation_types_exist(self):
        """Test that all expected violation types are defined."""
        assert SafetyViolationType.THRESHOLD_EXCEEDED.value == "threshold_exceeded"
        assert SafetyViolationType.ANOMALY_DETECTED.value == "anomaly_detected"
        assert SafetyViolationType.SELF_MODIFICATION.value == "self_modification_attempt"
        assert SafetyViolationType.RESOURCE_EXHAUSTION.value == "resource_exhaustion"
        assert SafetyViolationType.UNEXPECTED_BEHAVIOR.value == "unexpected_behavior"
        assert SafetyViolationType.CONSCIOUSNESS_RUNAWAY.value == "consciousness_runaway"
        assert SafetyViolationType.ETHICAL_VIOLATION.value == "ethical_violation"
        assert SafetyViolationType.GOAL_SPAM.value == "goal_spam"
        assert SafetyViolationType.AROUSAL_RUNAWAY.value == "arousal_runaway"
        assert SafetyViolationType.COHERENCE_COLLAPSE.value == "coherence_collapse"

    def test_violation_type_count(self):
        """Test that we have all expected violation types."""
        assert len(SafetyViolationType) == 10


class TestViolationType:
    """Test ViolationType enum (legacy)."""

    def test_all_legacy_violation_types_exist(self):
        """Test that all expected legacy violation types are defined."""
        assert ViolationType.ESGT_FREQUENCY_EXCEEDED.value == "esgt_frequency_exceeded"
        assert ViolationType.AROUSAL_SUSTAINED_HIGH.value == "arousal_sustained_high"
        assert ViolationType.UNEXPECTED_GOALS.value == "unexpected_goals"
        assert ViolationType.SELF_MODIFICATION.value == "self_modification"
        assert ViolationType.MEMORY_OVERFLOW.value == "memory_overflow"
        assert ViolationType.CPU_SATURATION.value == "cpu_saturation"
        assert ViolationType.ETHICAL_VIOLATION.value == "ethical_violation"
        assert ViolationType.UNKNOWN_BEHAVIOR.value == "unknown_behavior"

    def test_to_modern_conversion(self):
        """Test conversion from legacy ViolationType to modern SafetyViolationType."""
        assert ViolationType.ESGT_FREQUENCY_EXCEEDED.to_modern() == SafetyViolationType.THRESHOLD_EXCEEDED
        assert ViolationType.AROUSAL_SUSTAINED_HIGH.to_modern() == SafetyViolationType.AROUSAL_RUNAWAY
        assert ViolationType.UNEXPECTED_GOALS.to_modern() == SafetyViolationType.GOAL_SPAM
        assert ViolationType.SELF_MODIFICATION.to_modern() == SafetyViolationType.SELF_MODIFICATION
        assert ViolationType.MEMORY_OVERFLOW.to_modern() == SafetyViolationType.RESOURCE_EXHAUSTION
        assert ViolationType.CPU_SATURATION.to_modern() == SafetyViolationType.RESOURCE_EXHAUSTION
        assert ViolationType.ETHICAL_VIOLATION.to_modern() == SafetyViolationType.ETHICAL_VIOLATION
        assert ViolationType.UNKNOWN_BEHAVIOR.to_modern() == SafetyViolationType.UNEXPECTED_BEHAVIOR


class TestViolationTypeMappings:
    """Test violation type mapping dictionaries."""

    def test_legacy_to_modern_mapping_complete(self):
        """Test that all legacy types have modern mappings."""
        for legacy_type in ViolationType:
            assert legacy_type in _LEGACY_TO_MODERN_VIOLATION
            modern = _LEGACY_TO_MODERN_VIOLATION[legacy_type]
            assert isinstance(modern, SafetyViolationType)

    def test_modern_to_legacy_mapping_exists(self):
        """Test that modern to legacy mapping exists."""
        assert len(_MODERN_TO_LEGACY_VIOLATION) > 0
        for modern, legacy in _MODERN_TO_LEGACY_VIOLATION.items():
            assert isinstance(modern, SafetyViolationType)
            assert isinstance(legacy, ViolationType)

    def test_mapping_consistency(self):
        """Test that mappings are consistent."""
        for legacy, modern in _LEGACY_TO_MODERN_VIOLATION.items():
            # The reverse mapping should exist
            assert modern in _MODERN_TO_LEGACY_VIOLATION


class TestViolationTypeAdapter:
    """Test ViolationTypeAdapter."""

    def test_adapter_initialization(self):
        """Test adapter initialization."""
        modern = SafetyViolationType.THRESHOLD_EXCEEDED
        legacy = ViolationType.ESGT_FREQUENCY_EXCEEDED
        adapter = ViolationTypeAdapter(modern, legacy)

        assert adapter.modern == modern
        assert adapter.legacy == legacy

    def test_adapter_equality_with_modern(self):
        """Test adapter equality with modern violation type."""
        adapter = ViolationTypeAdapter(
            SafetyViolationType.THRESHOLD_EXCEEDED,
            ViolationType.ESGT_FREQUENCY_EXCEEDED
        )
        assert adapter == SafetyViolationType.THRESHOLD_EXCEEDED
        assert adapter != SafetyViolationType.ANOMALY_DETECTED

    def test_adapter_equality_with_legacy(self):
        """Test adapter equality with legacy violation type."""
        adapter = ViolationTypeAdapter(
            SafetyViolationType.THRESHOLD_EXCEEDED,
            ViolationType.ESGT_FREQUENCY_EXCEEDED
        )
        assert adapter == ViolationType.ESGT_FREQUENCY_EXCEEDED
        assert adapter != ViolationType.AROUSAL_SUSTAINED_HIGH

    def test_adapter_equality_with_adapter(self):
        """Test adapter equality with another adapter."""
        adapter1 = ViolationTypeAdapter(
            SafetyViolationType.THRESHOLD_EXCEEDED,
            ViolationType.ESGT_FREQUENCY_EXCEEDED
        )
        adapter2 = ViolationTypeAdapter(
            SafetyViolationType.THRESHOLD_EXCEEDED,
            ViolationType.ESGT_FREQUENCY_EXCEEDED
        )
        assert adapter1 == adapter2

    def test_adapter_equality_with_string(self):
        """Test adapter equality with string values."""
        adapter = ViolationTypeAdapter(
            SafetyViolationType.THRESHOLD_EXCEEDED,
            ViolationType.ESGT_FREQUENCY_EXCEEDED
        )
        # Check value strings
        assert adapter == "threshold_exceeded"
        assert adapter == "esgt_frequency_exceeded"
        # Check name strings
        assert adapter == "THRESHOLD_EXCEEDED"
        assert adapter == "ESGT_FREQUENCY_EXCEEDED"
        # Check non-matching
        assert adapter != "some_other_value"

    def test_adapter_hash(self):
        """Test adapter hashing."""
        adapter1 = ViolationTypeAdapter(
            SafetyViolationType.THRESHOLD_EXCEEDED,
            ViolationType.ESGT_FREQUENCY_EXCEEDED
        )
        adapter2 = ViolationTypeAdapter(
            SafetyViolationType.THRESHOLD_EXCEEDED,
            ViolationType.ESGT_FREQUENCY_EXCEEDED
        )
        # Same adapters should hash to same value
        assert hash(adapter1) == hash(adapter2)

    def test_adapter_repr(self):
        """Test adapter string representation."""
        adapter = ViolationTypeAdapter(
            SafetyViolationType.THRESHOLD_EXCEEDED,
            ViolationType.ESGT_FREQUENCY_EXCEEDED
        )
        repr_str = repr(adapter)
        assert "THRESHOLD_EXCEEDED" in repr_str or "threshold_exceeded" in repr_str

    def test_adapter_value_property(self):
        """Test adapter value property."""
        adapter = ViolationTypeAdapter(
            SafetyViolationType.THRESHOLD_EXCEEDED,
            ViolationType.ESGT_FREQUENCY_EXCEEDED
        )
        assert adapter.value == "threshold_exceeded"

    def test_adapter_name_property(self):
        """Test adapter name property."""
        adapter = ViolationTypeAdapter(
            SafetyViolationType.THRESHOLD_EXCEEDED,
            ViolationType.ESGT_FREQUENCY_EXCEEDED
        )
        assert adapter.name == "THRESHOLD_EXCEEDED"


class TestShutdownReason:
    """Test ShutdownReason enum."""

    def test_all_shutdown_reasons_exist(self):
        """Test that all expected shutdown reasons are defined."""
        assert ShutdownReason.MANUAL.value == "manual_operator_command"
        assert ShutdownReason.THRESHOLD.value == "threshold_violation"
        assert ShutdownReason.ANOMALY.value == "anomaly_detected"
        assert ShutdownReason.RESOURCE.value == "resource_exhaustion"
        assert ShutdownReason.TIMEOUT.value == "watchdog_timeout"
        assert ShutdownReason.ETHICAL.value == "ethical_violation"
        assert ShutdownReason.SELF_MODIFICATION.value == "self_modification_attempt"
        assert ShutdownReason.UNKNOWN.value == "unknown_cause"

    def test_shutdown_reason_count(self):
        """Test that we have all expected shutdown reasons."""
        assert len(ShutdownReason) == 8


# ==================== MODELS TESTS ====================


class TestSafetyViolation:
    """Test SafetyViolation data class."""

    def test_creation_with_modern_types(self):
        """Test creating violation with modern types."""
        violation = SafetyViolation(
            violation_id="test-001",
            violation_type=SafetyViolationType.THRESHOLD_EXCEEDED,
            threat_level=ThreatLevel.HIGH,
            timestamp=datetime.now(),
            description="Test violation"
        )

        assert violation.violation_id == "test-001"
        assert violation.modern_violation_type == SafetyViolationType.THRESHOLD_EXCEEDED
        assert violation.threat_level == ThreatLevel.HIGH
        assert violation.severity == SafetyLevel.CRITICAL

    def test_creation_with_legacy_types(self):
        """Test creating violation with legacy types."""
        violation = SafetyViolation(
            violation_id="test-002",
            violation_type=ViolationType.ESGT_FREQUENCY_EXCEEDED,
            severity=SafetyLevel.WARNING,
            timestamp=datetime.now()
        )

        assert violation.violation_id == "test-002"
        assert violation.legacy_violation_type == ViolationType.ESGT_FREQUENCY_EXCEEDED
        assert violation.severity == SafetyLevel.WARNING
        assert violation.modern_violation_type == SafetyViolationType.THRESHOLD_EXCEEDED

    def test_creation_with_string_types(self):
        """Test creating violation with string types."""
        violation = SafetyViolation(
            violation_id="test-003",
            violation_type="ESGT_FREQUENCY_EXCEEDED",
            threat_level="high",
            timestamp=1234567890.0
        )

        assert violation.violation_id == "test-003"
        assert violation.legacy_violation_type == ViolationType.ESGT_FREQUENCY_EXCEEDED
        assert violation.threat_level == ThreatLevel.HIGH

    def test_creation_with_timestamp_datetime(self):
        """Test creating violation with datetime timestamp."""
        now = datetime.now()
        violation = SafetyViolation(
            violation_id="test-004",
            violation_type=SafetyViolationType.ANOMALY_DETECTED,
            threat_level=ThreatLevel.MEDIUM,
            timestamp=now
        )

        assert violation.timestamp == now.timestamp()

    def test_creation_with_timestamp_float(self):
        """Test creating violation with float timestamp."""
        ts = 1234567890.0
        violation = SafetyViolation(
            violation_id="test-005",
            violation_type=SafetyViolationType.ANOMALY_DETECTED,
            threat_level=ThreatLevel.MEDIUM,
            timestamp=ts
        )

        assert violation.timestamp == ts

    def test_creation_with_all_fields(self):
        """Test creating violation with all optional fields."""
        violation = SafetyViolation(
            violation_id="test-006",
            violation_type=SafetyViolationType.RESOURCE_EXHAUSTION,
            threat_level=ThreatLevel.HIGH,
            timestamp=datetime.now(),
            description="CPU at 100%",
            metrics={"cpu": 100.0},
            source_component="test-component",
            automatic_action_taken="throttling",
            value_observed=100.0,
            threshold_violated=90.0,
            context={"process": "test"},
            message="CPU exceeded threshold"
        )

        assert violation.description == "CPU at 100%"
        assert violation.metrics["cpu"] == 100.0
        assert violation.source_component == "test-component"
        assert violation.automatic_action_taken == "throttling"
        assert violation.value_observed == 100.0
        assert violation.threshold_violated == 90.0
        assert violation.context == {"process": "test"}
        assert violation.message == "CPU exceeded threshold"

    def test_to_dict(self):
        """Test converting violation to dictionary."""
        now = datetime.now()
        violation = SafetyViolation(
            violation_id="test-007",
            violation_type=SafetyViolationType.THRESHOLD_EXCEEDED,
            threat_level=ThreatLevel.HIGH,
            timestamp=now,
            description="Test violation",
            metrics={"value": 100},
            value_observed=100.0,
            threshold_violated=80.0,
            context={"source": "test"}
        )

        data = violation.to_dict()

        assert data["violation_id"] == "test-007"
        assert data["threat_level"] == "high"
        assert data["severity"] == "critical"
        assert data["description"] == "Test violation"
        assert "timestamp_iso" in data
        assert data["value_observed"] == 100.0
        assert data["threshold_violated"] == 80.0
        assert data["context"] == {"source": "test"}

    def test_violation_type_adapter_property(self):
        """Test violation_type property returns adapter."""
        violation = SafetyViolation(
            violation_id="test-008",
            violation_type=SafetyViolationType.THRESHOLD_EXCEEDED,
            threat_level=ThreatLevel.HIGH,
            timestamp=datetime.now()
        )

        assert isinstance(violation.violation_type, ViolationTypeAdapter)
        assert violation.violation_type == SafetyViolationType.THRESHOLD_EXCEEDED

    def test_invalid_violation_type_raises_error(self):
        """Test that invalid violation type raises TypeError."""
        with pytest.raises(TypeError):
            SafetyViolation(
                violation_id="test-009",
                violation_type=12345,  # Invalid type
                threat_level=ThreatLevel.HIGH,
                timestamp=datetime.now()
            )

    def test_missing_severity_and_threat_raises_error(self):
        """Test that missing both severity and threat_level raises ValueError."""
        with pytest.raises(ValueError):
            SafetyViolation(
                violation_id="test-010",
                violation_type=SafetyViolationType.THRESHOLD_EXCEEDED,
                timestamp=datetime.now()
            )

    def test_invalid_timestamp_type_raises_error(self):
        """Test that invalid timestamp type raises TypeError."""
        with pytest.raises(TypeError):
            SafetyViolation(
                violation_id="test-011",
                violation_type=SafetyViolationType.THRESHOLD_EXCEEDED,
                threat_level=ThreatLevel.HIGH,
                timestamp="invalid"  # Invalid type
            )


class TestIncidentReport:
    """Test IncidentReport data class."""

    def test_creation(self):
        """Test creating an incident report."""
        violations = [
            SafetyViolation(
                violation_id="v1",
                violation_type=SafetyViolationType.THRESHOLD_EXCEEDED,
                threat_level=ThreatLevel.HIGH,
                timestamp=datetime.now()
            )
        ]

        report = IncidentReport(
            incident_id="incident-001",
            shutdown_reason=ShutdownReason.THRESHOLD,
            shutdown_timestamp=1234567890.0,
            violations=violations,
            system_state_snapshot={"state": "critical"},
            metrics_timeline=[{"time": 0, "value": 100}],
            recovery_possible=True,
            notes="Test incident"
        )

        assert report.incident_id == "incident-001"
        assert report.shutdown_reason == ShutdownReason.THRESHOLD
        assert report.shutdown_timestamp == 1234567890.0
        assert len(report.violations) == 1
        assert report.recovery_possible is True
        assert report.notes == "Test incident"

    def test_to_dict(self):
        """Test converting incident report to dictionary."""
        violations = [
            SafetyViolation(
                violation_id="v1",
                violation_type=SafetyViolationType.THRESHOLD_EXCEEDED,
                threat_level=ThreatLevel.HIGH,
                timestamp=datetime.now()
            )
        ]

        report = IncidentReport(
            incident_id="incident-002",
            shutdown_reason=ShutdownReason.ANOMALY,
            shutdown_timestamp=1234567890.0,
            violations=violations,
            system_state_snapshot={"cpu": 100},
            metrics_timeline=[],
            recovery_possible=False,
            notes="Critical failure"
        )

        data = report.to_dict()

        assert data["incident_id"] == "incident-002"
        assert data["shutdown_reason"] == "anomaly_detected"
        assert "shutdown_timestamp_iso" in data
        assert len(data["violations"]) == 1
        assert data["recovery_possible"] is False

    def test_save_to_disk(self):
        """Test saving incident report to disk."""
        violations = [
            SafetyViolation(
                violation_id="v1",
                violation_type=SafetyViolationType.THRESHOLD_EXCEEDED,
                threat_level=ThreatLevel.HIGH,
                timestamp=datetime.now()
            )
        ]

        report = IncidentReport(
            incident_id="incident-003",
            shutdown_reason=ShutdownReason.RESOURCE,
            shutdown_timestamp=1234567890.0,
            violations=violations,
            system_state_snapshot={},
            metrics_timeline=[],
            recovery_possible=True,
            notes="Test save"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            save_dir = Path(tmpdir) / "reports"
            filepath = report.save(directory=save_dir)

            assert filepath.exists()
            assert filepath.name == "incident-003.json"

            # Verify content
            with open(filepath) as f:
                loaded_data = json.load(f)
                assert loaded_data["incident_id"] == "incident-003"


class TestStateSnapshot:
    """Test StateSnapshot data class."""

    def test_creation_minimal(self):
        """Test creating snapshot with minimal fields."""
        now = datetime.now()
        snapshot = StateSnapshot(timestamp=now)

        assert snapshot.timestamp == now
        assert snapshot.esgt_state == {}
        assert snapshot.arousal_state == {}
        assert snapshot.violations == []

    def test_creation_complete(self):
        """Test creating snapshot with all fields."""
        now = datetime.now()
        violations = [
            SafetyViolation(
                violation_id="v1",
                violation_type=SafetyViolationType.THRESHOLD_EXCEEDED,
                threat_level=ThreatLevel.HIGH,
                timestamp=now
            )
        ]

        snapshot = StateSnapshot(
            timestamp=now,
            esgt_state={"sync": 0.8},
            arousal_state={"level": 0.5},
            mmei_state={"motivation": 0.7},
            tig_metrics={"phi": 0.9},
            recent_events=[{"event": "test"}],
            active_goals=[{"goal": "test"}],
            violations=violations
        )

        assert snapshot.esgt_state == {"sync": 0.8}
        assert snapshot.arousal_state == {"level": 0.5}
        assert len(snapshot.violations) == 1

    def test_to_dict(self):
        """Test converting snapshot to dictionary."""
        now = datetime.now()
        snapshot = StateSnapshot(
            timestamp=now,
            esgt_state={"sync": 0.8}
        )

        data = snapshot.to_dict()

        assert "timestamp" in data
        assert data["esgt_state"] == {"sync": 0.8}
        assert "violations" in data

    def test_from_dict_with_timestamp_float(self):
        """Test creating snapshot from dict with float timestamp."""
        data = {
            "timestamp": 1234567890.0,
            "esgt_state": {"sync": 0.8},
            "violations": []
        }

        snapshot = StateSnapshot.from_dict(data)

        assert isinstance(snapshot.timestamp, datetime)
        assert snapshot.esgt_state == {"sync": 0.8}

    def test_from_dict_with_timestamp_string(self):
        """Test creating snapshot from dict with ISO timestamp string."""
        now = datetime.now()
        data = {
            "timestamp": now.isoformat(),
            "mmei_state": {"motivation": 0.7}
        }

        snapshot = StateSnapshot.from_dict(data)

        assert isinstance(snapshot.timestamp, datetime)
        assert snapshot.mmei_state == {"motivation": 0.7}

    def test_from_dict_with_violations(self):
        """Test creating snapshot from dict with violations."""
        now = datetime.now()
        data = {
            "timestamp": now.timestamp(),
            "violations": [
                {
                    "violation_id": "v1",
                    "violation_type": "esgt_frequency_exceeded",  # Use value, not name
                    "severity": "warning",
                    "description": "Test violation"
                }
            ]
        }

        snapshot = StateSnapshot.from_dict(data)

        assert len(snapshot.violations) == 1
        assert isinstance(snapshot.violations[0], SafetyViolation)
        assert snapshot.violations[0].violation_id == "v1"

    def test_from_dict_with_violation_objects(self):
        """Test creating snapshot from dict with SafetyViolation objects."""
        now = datetime.now()
        violation = SafetyViolation(
            violation_id="v1",
            violation_type=SafetyViolationType.THRESHOLD_EXCEEDED,
            threat_level=ThreatLevel.HIGH,
            timestamp=now
        )

        data = {
            "timestamp": now.timestamp(),
            "violations": [violation]
        }

        snapshot = StateSnapshot.from_dict(data)

        assert len(snapshot.violations) == 1
        assert snapshot.violations[0] == violation

    def test_round_trip_serialization(self):
        """Test that snapshot can be serialized and deserialized without violations."""
        now = datetime.now()

        original = StateSnapshot(
            timestamp=now,
            esgt_state={"sync": 0.8},
            arousal_state={"level": 0.6},
            mmei_state={"motivation": 0.7},
            tig_metrics={"phi": 0.9},
            recent_events=[{"event": "test"}],
            active_goals=[{"goal": "achieve"}]
        )

        # Serialize to dict
        data = original.to_dict()

        # Deserialize
        restored = StateSnapshot.from_dict(data)

        assert restored.esgt_state == original.esgt_state
        assert restored.arousal_state == original.arousal_state
        assert restored.mmei_state == original.mmei_state
        assert restored.tig_metrics == original.tig_metrics
        assert len(restored.violations) == 0
