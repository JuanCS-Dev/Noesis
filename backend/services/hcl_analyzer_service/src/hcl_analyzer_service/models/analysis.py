"""
HCL Analyzer Service - Data Models
==================================

Pydantic models for analysis data structures.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class AnomalyType(str, Enum):
    """Enumeration for different types of anomalies detected."""

    SPIKE = "spike"
    DROP = "drop"
    TREND = "trend"
    OUTLIER = "outlier"


class Anomaly(BaseModel):
    """
    Represents a detected anomaly in system metrics.

    Attributes:
        type: The type of anomaly.
        metric_name: The name of the metric where the anomaly was detected.
        current_value: The current value of the metric.
        severity: The severity of the anomaly (0.0 to 1.0).
        description: A human-readable description of the anomaly.
    """

    type: AnomalyType
    metric_name: str
    current_value: float
    severity: float
    description: str


class AnalysisResult(BaseModel):
    """
    Represents the comprehensive analysis of system resources and health.

    Attributes:
        timestamp: ISO formatted timestamp of the analysis.
        overall_health_score: An aggregated score representing system health (0.0 to 1.0).
        anomalies: A list of detected anomalies.
        trends: Identified trends in system metrics.
        recommendations: Suggested actions based on the analysis.
        requires_intervention: True if the analysis indicates a need for intervention.
    """

    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    overall_health_score: float
    anomalies: List[Anomaly]
    trends: Dict[str, Any]
    recommendations: List[str]
    requires_intervention: bool


class SystemMetrics(BaseModel):
    """
    Represents a snapshot of system metrics collected by the HCL Monitor.

    Attributes:
        timestamp: ISO formatted timestamp of when the metrics were collected.
        cpu_usage: Current CPU utilization (0-100%).
        memory_usage: Current memory utilization (0-100%).
        disk_io_rate: Disk I/O rate (bytes/sec).
        network_io_rate: Network I/O rate (bytes/sec).
        avg_latency_ms: Average system latency in milliseconds.
        error_rate: Rate of errors in the system.
        service_status: Status of various sub-services.
    """

    timestamp: str
    cpu_usage: float
    memory_usage: float
    disk_io_rate: float
    network_io_rate: float
    avg_latency_ms: float
    error_rate: float
    service_status: Dict[str, str]
