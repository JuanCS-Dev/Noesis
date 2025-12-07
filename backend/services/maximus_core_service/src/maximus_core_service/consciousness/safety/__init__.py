"""
MAXIMUS Safety Core - Modular Safety System

This package provides the fundamental safety layer for MAXIMUS consciousness.
All components are production-ready and follow DOUTRINA VÉRTICE v2.0.

Components:
-----------
- Enums: ThreatLevel, SafetyLevel, SafetyViolationType, ViolationType, ShutdownReason
- Thresholds: SafetyThresholds (immutable configuration)
- Models: SafetyViolation, IncidentReport, StateSnapshot
- KillSwitch: Emergency shutdown (<1s guaranteed)
- ThresholdMonitor: Hard limit monitoring
- AnomalyDetector: Statistical anomaly detection
- ConsciousnessSafetyProtocol: Main orchestrator

Usage:
------
    from consciousness.safety import ConsciousnessSafetyProtocol, SafetyThresholds

    thresholds = SafetyThresholds(
        esgt_frequency_max_hz=10.0,
        arousal_max=0.95
    )

    safety = ConsciousnessSafetyProtocol(consciousness_system, thresholds)
    await safety.start_monitoring()

Safety Guarantees:
-----------------
- Kill switch: <1s shutdown (validated via test)
- Standalone operation: Zero external dependencies
- Immutable thresholds: Cannot be modified at runtime
- Fail-safe design: Last resort = SIGTERM
- Complete observability: All metrics exposed

Version: 2.0.0 - Production Hardened
Status: DOUTRINA VÉRTICE v2.0 COMPLIANT
"""

from __future__ import annotations

from .anomaly_detector import AnomalyDetector
from .enums import (
    SafetyLevel,
    SafetyViolationType,
    ShutdownReason,
    ThreatLevel,
    ViolationType,
    ViolationTypeAdapter,
)

# Backward compatibility alias (tests use underscore prefix)
_ViolationTypeAdapter = ViolationTypeAdapter
from .kill_switch import KillSwitch
from .models import IncidentReport, SafetyViolation, StateSnapshot
from .protocol import ConsciousnessSafetyProtocol
from .threshold_monitor import ThresholdMonitor
from .thresholds import SafetyThresholds

__all__ = [
    # Enums
    "ThreatLevel",
    "SafetyLevel",
    "SafetyViolationType",
    "ViolationType",
    "ViolationTypeAdapter",
    "_ViolationTypeAdapter",  # Backward compatibility
    "ShutdownReason",
    # Configuration
    "SafetyThresholds",
    # Models
    "SafetyViolation",
    "IncidentReport",
    "StateSnapshot",
    # Components
    "KillSwitch",
    "ThresholdMonitor",
    "AnomalyDetector",
    # Main Protocol
    "ConsciousnessSafetyProtocol",
]

__version__ = "2.0.0"
__status__ = "Production Hardened"
