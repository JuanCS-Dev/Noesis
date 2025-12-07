"""
Safety Enums - Threat levels and violation types.

Part of the MAXIMUS Safety Core module.

Exports:
- ThreatLevel: Modern five-level threat severity
- SafetyLevel: Legacy four-level severity (backward compatibility)
- SafetyViolationType: Modern violation types
- ViolationType: Legacy violation types (backward compatibility)
- ViolationTypeAdapter: Adapter for cross-compatibility
- ShutdownReason: Reasons for emergency shutdown
- Mapping dictionaries for conversion between legacy and modern types
"""

from __future__ import annotations

from enum import Enum

__all__ = [
    "ThreatLevel",
    "SafetyLevel",
    "SafetyViolationType",
    "ViolationType",
    "ViolationTypeAdapter",
    "ShutdownReason",
    "_LEGACY_TO_MODERN_VIOLATION",
    "_MODERN_TO_LEGACY_VIOLATION",
]


class ThreatLevel(Enum):
    """
    Threat severity levels for safety violations.

    NONE: No threat detected (normal operation)
    LOW: Minor deviation, log only
    MEDIUM: Significant deviation, alert HITL
    HIGH: Dangerous state, initiate graceful degradation
    CRITICAL: Imminent danger, trigger kill switch
    """

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SafetyLevel(Enum):
    """
    Legacy safety severity levels (backward compatibility).

    Maps the historical four-level scale to the modern five-level ThreatLevel.
    """

    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

    @classmethod
    def from_threat(cls, threat_level: ThreatLevel) -> SafetyLevel:
        """Convert a modern threat level into the legacy severity scale."""
        mapping = {
            ThreatLevel.NONE: cls.NORMAL,
            ThreatLevel.LOW: cls.WARNING,
            ThreatLevel.MEDIUM: cls.WARNING,
            ThreatLevel.HIGH: cls.CRITICAL,
            ThreatLevel.CRITICAL: cls.EMERGENCY,
        }
        return mapping[threat_level]

    def to_threat(self) -> ThreatLevel:
        """Convert the legacy severity scale back to a modern threat level."""
        mapping = {
            SafetyLevel.NORMAL: ThreatLevel.NONE,
            SafetyLevel.WARNING: ThreatLevel.LOW,
            SafetyLevel.CRITICAL: ThreatLevel.HIGH,
            SafetyLevel.EMERGENCY: ThreatLevel.CRITICAL,
        }
        return mapping[self]


class SafetyViolationType(Enum):
    """
    Types of safety violations.

    Each violation type maps to specific thresholds and response protocols.
    """

    THRESHOLD_EXCEEDED = "threshold_exceeded"
    ANOMALY_DETECTED = "anomaly_detected"
    SELF_MODIFICATION = "self_modification_attempt"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    UNEXPECTED_BEHAVIOR = "unexpected_behavior"
    CONSCIOUSNESS_RUNAWAY = "consciousness_runaway"
    ETHICAL_VIOLATION = "ethical_violation"
    GOAL_SPAM = "goal_spam"
    AROUSAL_RUNAWAY = "arousal_runaway"
    COHERENCE_COLLAPSE = "coherence_collapse"


class ViolationType(Enum):
    """
    Legacy safety violation types (backward compatibility).

    These map directly onto the modern SafetyViolationType enum.
    """

    ESGT_FREQUENCY_EXCEEDED = "esgt_frequency_exceeded"
    AROUSAL_SUSTAINED_HIGH = "arousal_sustained_high"
    UNEXPECTED_GOALS = "unexpected_goals"
    SELF_MODIFICATION = "self_modification"
    MEMORY_OVERFLOW = "memory_overflow"
    CPU_SATURATION = "cpu_saturation"
    ETHICAL_VIOLATION = "ethical_violation"
    UNKNOWN_BEHAVIOR = "unknown_behavior"

    def to_modern(self) -> SafetyViolationType:
        """Translate the legacy violation enum to the modern equivalent."""
        return _LEGACY_TO_MODERN_VIOLATION[self]


_LEGACY_TO_MODERN_VIOLATION = {
    ViolationType.ESGT_FREQUENCY_EXCEEDED: SafetyViolationType.THRESHOLD_EXCEEDED,
    ViolationType.AROUSAL_SUSTAINED_HIGH: SafetyViolationType.AROUSAL_RUNAWAY,
    ViolationType.UNEXPECTED_GOALS: SafetyViolationType.GOAL_SPAM,
    ViolationType.SELF_MODIFICATION: SafetyViolationType.SELF_MODIFICATION,
    ViolationType.MEMORY_OVERFLOW: SafetyViolationType.RESOURCE_EXHAUSTION,
    ViolationType.CPU_SATURATION: SafetyViolationType.RESOURCE_EXHAUSTION,
    ViolationType.ETHICAL_VIOLATION: SafetyViolationType.ETHICAL_VIOLATION,
    ViolationType.UNKNOWN_BEHAVIOR: SafetyViolationType.UNEXPECTED_BEHAVIOR,
}

_MODERN_TO_LEGACY_VIOLATION: dict[SafetyViolationType, ViolationType] = {}
for _legacy, _modern in _LEGACY_TO_MODERN_VIOLATION.items():
    _MODERN_TO_LEGACY_VIOLATION.setdefault(_modern, _legacy)


class ViolationTypeAdapter:
    """Adapter that allows equality across legacy and modern violation enums."""

    __slots__ = ("modern", "legacy")

    def __init__(self, modern: SafetyViolationType, legacy: ViolationType):
        """Initialize adapter with both enum types."""
        self.modern = modern
        self.legacy = legacy

    def __eq__(self, other: object) -> bool:
        """Check equality with various types."""
        if isinstance(other, ViolationTypeAdapter):
            return self.modern is other.modern
        if isinstance(other, SafetyViolationType):
            return self.modern is other
        if isinstance(other, ViolationType):
            return self.legacy is other
        if isinstance(other, str):
            return other in {
                self.modern.value,
                self.legacy.value,
                self.modern.name,
                self.legacy.name,
            }
        return False

    def __hash__(self) -> int:
        """Hash based on modern type."""
        return hash(self.modern)

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.modern}"

    @property
    def value(self) -> str:
        """Get the value string."""
        return self.modern.value

    @property
    def name(self) -> str:
        """Get the name string."""
        return self.modern.name


class ShutdownReason(Enum):
    """
    Reasons for emergency shutdown.

    Used for incident classification and recovery assessment.
    """

    MANUAL = "manual_operator_command"
    THRESHOLD = "threshold_violation"
    ANOMALY = "anomaly_detected"
    RESOURCE = "resource_exhaustion"
    TIMEOUT = "watchdog_timeout"
    ETHICAL = "ethical_violation"
    SELF_MODIFICATION = "self_modification_attempt"
    UNKNOWN = "unknown_cause"
