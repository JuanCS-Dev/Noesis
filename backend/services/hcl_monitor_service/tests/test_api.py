"""
Unit tests for HCL Monitor Service API.
"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from backend.services.hcl_monitor_service.api.dependencies import get_collector
from backend.services.hcl_monitor_service.core.collector import SystemMetricsCollector
from backend.services.hcl_monitor_service.main import app
from backend.services.hcl_monitor_service.models.metrics import SystemMetrics

client = TestClient(app)


def test_health_check() -> None:
    """Test health check endpoint."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root() -> None:
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Operational" in response.json()["message"]


@pytest.mark.asyncio
async def test_get_latest_metrics() -> None:
    """Test get latest metrics endpoint."""
    # Mock collector
    mock_collector = AsyncMock(spec=SystemMetricsCollector)
    mock_metrics = SystemMetrics(
        timestamp=datetime.now(),
        cpu_usage=50.0,
        memory_usage=60.0,
        disk_io_read_rate=100.0,
        disk_io_write_rate=100.0,
        network_io_recv_rate=100.0,
        network_io_sent_rate=100.0,
        avg_latency_ms=10.0,
        error_rate=0.0,
        service_status={"test": "ok"}
    )
    mock_collector.get_latest_metrics.return_value = mock_metrics

    app.dependency_overrides[get_collector] = lambda: mock_collector

    response = client.get("/v1/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["cpu_usage"] == 50.0

    # Reset overrides
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_get_metrics_history() -> None:
    """Test get metrics history endpoint."""
    # Mock collector
    mock_collector = AsyncMock(spec=SystemMetricsCollector)
    mock_metrics = SystemMetrics(
        timestamp=datetime.now(),
        cpu_usage=50.0,
        memory_usage=60.0,
        disk_io_read_rate=100.0,
        disk_io_write_rate=100.0,
        network_io_recv_rate=100.0,
        network_io_sent_rate=100.0,
        avg_latency_ms=10.0,
        error_rate=0.0,
        service_status={"test": "ok"}
    )
    mock_collector.get_metrics_history.return_value = [mock_metrics]

    app.dependency_overrides[get_collector] = lambda: mock_collector

    response = client.get("/v1/metrics/history")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["cpu_usage"] == 50.0

    # Reset overrides
    app.dependency_overrides = {}
