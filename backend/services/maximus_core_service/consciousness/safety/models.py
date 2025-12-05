"""
Safety Models - Data classes for safety violations and incident reporting.

This module contains the core data structures used throughout the safety system:
- SafetyViolation: Records of safety violations with backward compatibility
- IncidentReport: Complete incident reports for post-mortem analysis
- StateSnapshot: Legacy state snapshot representation
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .enums import (
    SafetyLevel,
    SafetyViolationType,
    ShutdownReason,
    ThreatLevel,
    ViolationType,
    ViolationTypeAdapter as _ViolationTypeAdapter,
    _LEGACY_TO_MODERN_VIOLATION,
    _MODERN_TO_LEGACY_VIOLATION,
)

logger = logging.getLogger(__name__)


# ==================== SAFETY VIOLATION ====================


@dataclass(eq=True, init=False)
class SafetyViolation:
    """
    Record of a safety violation.

    Provides backward-compatible accessors for legacy tests while preserving
    the richer telemetry captured by the modern safety core.
    """

    violation_id: str = field(init=False)
    violation_type: _ViolationTypeAdapter = field(init=False)
    threat_level: ThreatLevel = field(init=False)
    timestamp: float = field(init=False)  # Unix timestamp
    description: str = field(init=False)
    metrics: dict[str, Any] = field(init=False)
    source_component: str = field(init=False)
    automatic_action_taken: str | None = field(init=False)
    context: dict[str, Any] = field(init=False, repr=False)
    value_observed: Any = field(init=False, repr=False)
    threshold_violated: Any = field(init=False, repr=False)
    message: str = field(init=False, repr=False)

    _severity: SafetyLevel = field(init=False, repr=False)
    _modern_violation_type: SafetyViolationType = field(init=False, repr=False)
    _legacy_violation_type: ViolationType = field(init=False, repr=False)
    _timestamp_dt: datetime = field(init=False, repr=False)

    def __init__(
        self,
        *,
        violation_id: str,
        violation_type: SafetyViolationType | ViolationType | str,
        threat_level: ThreatLevel | SafetyLevel | str | None = None,
        severity: SafetyLevel | ThreatLevel | str | None = None,
        timestamp: float | int | datetime,
        description: str | None = None,
        metrics: dict[str, Any] | None = None,
        source_component: str = "consciousness-safety",
        automatic_action_taken: str | None = None,
        value_observed: Any | None = None,
        threshold_violated: Any | None = None,
        context: dict[str, Any] | None = None,
        message: str | None = None,
    ):
        # Normalize violation type
        legacy_violation: ViolationType
        modern_violation: SafetyViolationType

        if isinstance(violation_type, SafetyViolationType):
            modern_violation = violation_type
            legacy_violation = _MODERN_TO_LEGACY_VIOLATION.get(
                modern_violation, ViolationType.UNKNOWN_BEHAVIOR
            )
        else:
            if isinstance(violation_type, str):
                try:
                    legacy_violation = ViolationType[violation_type]
                except KeyError:
                    legacy_violation = ViolationType(violation_type)
            elif isinstance(violation_type, ViolationType):
                legacy_violation = violation_type
            else:
                raise TypeError("violation_type must be SafetyViolationType, ViolationType, or str")
            modern_violation = _LEGACY_TO_MODERN_VIOLATION.get(
                legacy_violation, SafetyViolationType.UNEXPECTED_BEHAVIOR
            )

        # Normalize severity / threat level
        legacy_severity: SafetyLevel | None = None
        modern_threat: ThreatLevel | None = None

        if threat_level is not None:
            if isinstance(threat_level, ThreatLevel):
                modern_threat = threat_level
                legacy_severity = SafetyLevel.from_threat(threat_level)
            elif isinstance(threat_level, SafetyLevel):
                legacy_severity = threat_level
                modern_threat = threat_level.to_threat()
            elif isinstance(threat_level, str):
                modern_threat = ThreatLevel(threat_level)
                legacy_severity = SafetyLevel.from_threat(modern_threat)
            else:
                raise TypeError("Unsupported threat_level type")

        if severity is not None:
            if isinstance(severity, SafetyLevel):
                legacy_severity = severity
                modern_threat = severity.to_threat()
            elif isinstance(severity, ThreatLevel):
                modern_threat = severity
                legacy_severity = SafetyLevel.from_threat(severity)
            elif isinstance(severity, str):
                legacy_severity = SafetyLevel(severity)
                modern_threat = legacy_severity.to_threat()
            else:
                raise TypeError("Unsupported severity type")

        if modern_threat is None or legacy_severity is None:
            raise ValueError("Either threat_level or severity must be provided")

        # Normalize timestamp
        if isinstance(timestamp, datetime):
            timestamp_value = timestamp.timestamp()
            timestamp_dt = timestamp
        elif isinstance(timestamp, (int, float)):
            timestamp_value = float(timestamp)
            timestamp_dt = datetime.fromtimestamp(timestamp_value)
        else:
            raise TypeError("timestamp must be datetime or numeric")

        metrics_dict = dict(metrics) if metrics else {}
        context_dict = dict(context) if context else {}

        if value_observed is not None:
            metrics_dict.setdefault("value_observed", value_observed)

        if threshold_violated is not None:
            metrics_dict.setdefault("threshold_violated", threshold_violated)

        if context_dict:
            metrics_dict.setdefault("context", context_dict)

        description_text = description or message or "Safety violation recorded"
        message_text = message or description_text

        object.__setattr__(self, "violation_id", violation_id)
        adapter = _ViolationTypeAdapter(modern_violation, legacy_violation)
        object.__setattr__(self, "violation_type", adapter)
        object.__setattr__(self, "_modern_violation_type", modern_violation)
        object.__setattr__(self, "_legacy_violation_type", legacy_violation)
        object.__setattr__(self, "threat_level", modern_threat)
        object.__setattr__(self, "_severity", legacy_severity)
        object.__setattr__(self, "timestamp", timestamp_value)
        object.__setattr__(self, "_timestamp_dt", timestamp_dt)
        object.__setattr__(self, "description", description_text)
        object.__setattr__(self, "metrics", metrics_dict)
        object.__setattr__(self, "source_component", source_component)
        object.__setattr__(self, "automatic_action_taken", automatic_action_taken)
        object.__setattr__(self, "context", context_dict)
        object.__setattr__(self, "value_observed", value_observed)
        object.__setattr__(self, "threshold_violated", threshold_violated)
        object.__setattr__(self, "message", message_text)

    @property
    def severity(self) -> SafetyLevel:
        """Legacy severity accessor."""
        return self._severity

    @property
    def safety_violation_type(self) -> SafetyViolationType:
        """Modern safety violation enum accessor."""
        return self._modern_violation_type

    @property
    def modern_violation_type(self) -> SafetyViolationType:
        """Alias for the modern safety violation enum accessor."""
        return self._modern_violation_type

    @property
    def legacy_violation_type(self) -> ViolationType:
        """Legacy violation enum accessor."""
        return self._legacy_violation_type

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data: dict[str, Any] = {
            "violation_id": self.violation_id,
            "violation_type": self.violation_type.value,
            "legacy_violation_type": self.legacy_violation_type.value,
            "threat_level": self.threat_level.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp,
            "timestamp_iso": self._timestamp_dt.isoformat(),
            "description": self.description,
            "metrics": self.metrics,
            "source_component": self.source_component,
            "automatic_action_taken": self.automatic_action_taken,
        }

        if self.value_observed is not None:
            data["value_observed"] = self.value_observed

        if self.threshold_violated is not None:
            data["threshold_violated"] = self.threshold_violated

        if self.context:
            data["context"] = self.context

        if self.message:
            data["message"] = self.message

        return data


# ==================== INCIDENT REPORT ====================


@dataclass
class IncidentReport:
    """
    Complete incident report for post-mortem analysis.

    Generated automatically on emergency shutdown.
    Provides full context for debugging and safety improvements.
    """

    incident_id: str
    shutdown_reason: ShutdownReason
    shutdown_timestamp: float
    violations: list[SafetyViolation]
    system_state_snapshot: dict[str, Any]
    metrics_timeline: list[dict[str, Any]]
    recovery_possible: bool
    notes: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "incident_id": self.incident_id,
            "shutdown_reason": self.shutdown_reason.value,
            "shutdown_timestamp": self.shutdown_timestamp,
            "shutdown_timestamp_iso": datetime.fromtimestamp(self.shutdown_timestamp).isoformat(),
            "violations": [v.to_dict() for v in self.violations],
            "system_state_snapshot": self.system_state_snapshot,
            "metrics_timeline": self.metrics_timeline,
            "recovery_possible": self.recovery_possible,
            "notes": self.notes,
        }

    def save(self, directory: Path = Path("consciousness/incident_reports")) -> Path:
        """
        Save incident report to disk.

        Args:
            directory: Directory to save report

        Returns:
            Path to saved report file
        """
        directory.mkdir(parents=True, exist_ok=True)

        filename = f"{self.incident_id}.json"
        filepath = directory / filename

        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

        logger.info(f"Incident report saved: {filepath}")
        return filepath


# ==================== STATE SNAPSHOT ====================


@dataclass
class StateSnapshot:
    """
    Legacy state snapshot representation (backward compatibility).

    Newer code uses lightweight dictionaries for speed; this dataclass
    keeps the historical API surface available for tests and tooling.
    """

    timestamp: datetime
    esgt_state: dict[str, Any] = field(default_factory=dict)
    arousal_state: dict[str, Any] = field(default_factory=dict)
    mmei_state: dict[str, Any] = field(default_factory=dict)
    tig_metrics: dict[str, Any] = field(default_factory=dict)
    recent_events: list[dict[str, Any]] = field(default_factory=list)
    active_goals: list[dict[str, Any]] = field(default_factory=list)
    violations: list[SafetyViolation] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the snapshot to a dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "esgt_state": self.esgt_state,
            "arousal_state": self.arousal_state,
            "mmei_state": self.mmei_state,
            "tig_metrics": self.tig_metrics,
            "recent_events": self.recent_events,
            "active_goals": self.active_goals,
            "violations": [
                violation.to_dict() if hasattr(violation, "to_dict") else violation
                for violation in self.violations
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StateSnapshot:
        """Create a snapshot from a dictionary payload."""
        timestamp_value = data.get("timestamp")
        if isinstance(timestamp_value, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp_value)
        elif isinstance(timestamp_value, str):
            timestamp = datetime.fromisoformat(timestamp_value)
        else:
            timestamp = datetime.now()

        violations_data = data.get("violations", [])
        violations: list[SafetyViolation] = []
        for violation in violations_data:
            if isinstance(violation, SafetyViolation):
                violations.append(violation)
            elif isinstance(violation, dict):
                violations.append(
                    SafetyViolation(
                        violation_id=violation.get("violation_id", "legacy"),
                        violation_type=(
                            ViolationType(
                                violation.get(
                                    "violation_type", ViolationType.UNKNOWN_BEHAVIOR.value
                                )
                            )
                            if isinstance(violation.get("violation_type"), str)
                            else violation.get("violation_type", ViolationType.UNKNOWN_BEHAVIOR)
                        ),
                        severity=(
                            SafetyLevel(violation.get("severity", SafetyLevel.WARNING.value))
                            if isinstance(violation.get("severity"), str)
                            else violation.get("severity", SafetyLevel.WARNING)
                        ),
                        timestamp=timestamp,
                        description=violation.get("description"),
                        metrics=violation.get("metrics"),
                        source_component=violation.get("source_component", "legacy-state-snapshot"),
                        value_observed=violation.get("value_observed"),
                        threshold_violated=violation.get("threshold_violated"),
                        context=violation.get("context"),
                        message=violation.get("message"),
                    )
                )

        return cls(
            timestamp=timestamp,
            esgt_state=data.get("esgt_state", {}),
            arousal_state=data.get("arousal_state", {}),
            mmei_state=data.get("mmei_state", {}),
            tig_metrics=data.get("tig_metrics", {}),
            recent_events=data.get("recent_events", []),
            active_goals=data.get("active_goals", []),
            violations=violations,
        )
