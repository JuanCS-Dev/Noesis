"""Shim for fairness.monitor backward compatibility."""
from .monitor_legacy import (
    FairnessMonitor,
    FairnessAlert,
    FairnessSnapshot,
    FairnessMetric,
    BiasDetectionResult,
)

__all__ = [
    "FairnessMonitor",
    "FairnessAlert",
    "FairnessSnapshot",
    "FairnessMetric",
    "BiasDetectionResult",
]
