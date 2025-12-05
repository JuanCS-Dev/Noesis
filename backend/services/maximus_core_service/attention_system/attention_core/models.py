"""Attention Core Models.

Data structures for peripheral and foveal attention processing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PeripheralDetection:
    """Result from peripheral scanning.

    Attributes:
        target_id: Unique identifier for the detection target.
        detection_type: Type of detection (statistical_anomaly, entropy_change, volume_spike).
        confidence: Detection confidence (0.0-1.0).
        timestamp: Unix timestamp of detection.
        metadata: Additional detection metadata.
    """

    target_id: str
    detection_type: str
    confidence: float
    timestamp: float
    metadata: dict[str, Any]


@dataclass
class FovealAnalysis:
    """Result from foveal deep analysis.

    Attributes:
        target_id: Target identifier.
        threat_level: BENIGN, SUSPICIOUS, MALICIOUS, or CRITICAL.
        confidence: Analysis confidence (0.0-1.0).
        findings: List of analysis findings.
        analysis_time_ms: Time taken for analysis in milliseconds.
        timestamp: Unix timestamp of analysis.
        recommended_actions: List of recommended actions.
    """

    target_id: str
    threat_level: str
    confidence: float
    findings: list[dict[str, Any]]
    analysis_time_ms: float
    timestamp: float
    recommended_actions: list[str]
