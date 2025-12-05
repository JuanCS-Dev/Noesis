"""
Unit tests for HCL Analyzer API.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock
import pytest
from fastapi.testclient import TestClient
from backend.services.hcl_analyzer_service.main import app
from backend.services.hcl_analyzer_service.core.analyzer import SystemAnalyzer
from backend.services.hcl_analyzer_service.models.analysis import AnalysisResult

client = TestClient(app)

def test_health_check() -> None:
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_metrics() -> None:
    """Test metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "analyzer_active 1" in response.text

@pytest.mark.asyncio
async def test_analyze_endpoint() -> None:
    """Test analyze endpoint."""
    # Mock dependency injection
    async def override_get_analyzer() -> AsyncMock:
        mock = AsyncMock(spec=SystemAnalyzer)
        mock.analyze_metrics.return_value = AnalysisResult(
            overall_health_score=0.9,
            anomalies=[],
            trends={},
            recommendations=[],
            requires_intervention=False
        )
        return mock

    from backend.services.hcl_analyzer_service.api.dependencies import get_analyzer  # pylint: disable=import-outside-toplevel
    app.dependency_overrides[get_analyzer] = override_get_analyzer

    payload = {
        "timestamp": datetime.now().isoformat(),
        "cpu_usage": 50.0,
        "memory_usage": 60.0,
        "disk_io_rate": 1000.0,
        "network_io_rate": 2000.0,
        "avg_latency_ms": 100.0,
        "error_rate": 0.01,
        "service_status": {"db": "up"}
    }

    response = client.post("/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["overall_health_score"] == 0.9
