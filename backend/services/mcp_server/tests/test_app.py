"""
Tests for FastAPI Application.

Integration tests for main.py FastAPI app.
Follows CODE_CONSTITUTION: 100% type hints, Google style.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_returns_ok(self) -> None:
        """HYPOTHESIS: /health returns 200 with status ok."""
        from main import app

        client: TestClient = TestClient(app)
        response: Response = client.get("/health")

        assert response.status_code == 200
        data: Dict[str, Any] = response.json()
        assert data["status"] == "ok"
        assert "service" in data


class TestMetricsEndpoint:
    """Test metrics endpoint."""

    def test_metrics_returns_stats(self) -> None:
        """HYPOTHESIS: /metrics returns circuit breaker stats."""
        from main import app

        client: TestClient = TestClient(app)
        response: Response = client.get("/metrics")

        assert response.status_code == 200
        data: Dict[str, Any] = response.json()
        assert "circuit_breakers" in data


class TestAppStartup:
    """Test app startup."""

    def test_app_imports_successfully(self) -> None:
        """HYPOTHESIS: App can be imported without errors."""
        from main import app

        assert app is not None
        assert app.title == "MAXIMUS MCP Server"
