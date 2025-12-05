"""
Unit tests for System Analyzer.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from backend.services.hcl_analyzer_service.core.analyzer import SystemAnalyzer
from backend.services.hcl_analyzer_service.config import AnalyzerSettings
from backend.services.hcl_analyzer_service.models.analysis import (
    SystemMetrics,
    AnomalyType,
)

@pytest.fixture(name="analyzer")
def fixture_analyzer() -> SystemAnalyzer:
    """Analyzer fixture."""
    settings = AnalyzerSettings(anomaly_threshold=0.8, history_window_size=100)
    return SystemAnalyzer(settings)

@pytest.mark.asyncio
async def test_analyze_healthy_metrics(analyzer: SystemAnalyzer) -> None:
    """Test analyzing healthy metrics."""
    metrics = SystemMetrics(
        timestamp=datetime.now().isoformat(),
        cpu_usage=50.0,
        memory_usage=60.0,
        disk_io_rate=1000.0,
        network_io_rate=2000.0,
        avg_latency_ms=100.0,
        error_rate=0.01,
        service_status={"db": "up"}
    )

    result = await analyzer.analyze_metrics(metrics)

    assert result.overall_health_score == 1.0
    assert len(result.anomalies) == 0
    assert result.requires_intervention is False

@pytest.mark.asyncio
async def test_analyze_critical_cpu(analyzer: SystemAnalyzer) -> None:
    """Test analyzing critical CPU usage."""
    metrics = SystemMetrics(
        timestamp=datetime.now().isoformat(),
        cpu_usage=95.0,
        memory_usage=60.0,
        disk_io_rate=1000.0,
        network_io_rate=2000.0,
        avg_latency_ms=100.0,
        error_rate=0.01,
        service_status={"db": "up"}
    )

    result = await analyzer.analyze_metrics(metrics)

    assert len(result.anomalies) == 1
    assert result.anomalies[0].type == AnomalyType.SPIKE
    assert result.anomalies[0].metric_name == "cpu_usage"
    assert result.overall_health_score < 1.0

@pytest.mark.asyncio
async def test_analyze_multiple_issues(analyzer: SystemAnalyzer) -> None:
    """Test analyzing multiple issues."""
    metrics = SystemMetrics(
        timestamp=datetime.now().isoformat(),
        cpu_usage=95.0,
        memory_usage=95.0,
        disk_io_rate=1000.0,
        network_io_rate=2000.0,
        avg_latency_ms=600.0,
        error_rate=0.06,
        service_status={"db": "up"}
    )

    result = await analyzer.analyze_metrics(metrics)

    # Should have CPU, Memory, and Error Rate anomalies
    assert len(result.anomalies) == 3
    # Latency penalty should also apply
    assert result.overall_health_score < 0.8
    assert result.requires_intervention is True
