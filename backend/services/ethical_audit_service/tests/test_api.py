"""
Unit tests for Ethical Audit Service API.
"""

from __future__ import annotations


from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from api.dependencies import (
    get_detector,
    get_validator
)
from core.constitutional_validator import (
    ConstitutionalValidator
)
from core.violation_detector import (
    ViolationDetector
)
from main import app
from models.audit import (
    ComplianceReport,
    Violation,
    ViolationSeverity,
    ViolationType
)

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
    assert "Guardian Agent" in response.json()["message"]


@pytest.mark.asyncio
async def test_validate_operation() -> None:
    """Test validate operation endpoint."""
    # Mock validator and detector
    mock_validator = AsyncMock(spec=ConstitutionalValidator)
    mock_detector = AsyncMock(spec=ViolationDetector)

    mock_validator.validate_operation.return_value = (True, [])

    app.dependency_overrides[get_validator] = lambda: mock_validator
    app.dependency_overrides[get_detector] = lambda: mock_detector

    response = client.post(
        "/v1/validate",
        params={"service": "test", "operation": "test_op"},
        json={"data": "clean"}
    )

    assert response.status_code == 200
    assert response.json()["is_valid"] is True

    # Reset overrides
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_record_violation() -> None:
    """Test record violation endpoint."""
    # Mock detector
    mock_detector = AsyncMock(spec=ViolationDetector)

    app.dependency_overrides[get_detector] = lambda: mock_detector

    violation_data = {
        "violation_id": "test-v1",
        "violation_type": "placeholder_code",
        "severity": "high",
        "description": "Test violation",
        "service": "test-service"
    }

    response = client.post("/v1/violations", json=violation_data)

    assert response.status_code == 200
    assert response.json()["status"] == "recorded"

    # Reset overrides
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_get_compliance_report() -> None:
    """Test get compliance report endpoint."""
    # Mock detector
    mock_detector = AsyncMock(spec=ViolationDetector)
    mock_report = ComplianceReport(
        report_id="test-report",
        service="test",
        total_checks=10,
        passed_checks=10,
        violations=[],
        compliance_score=1.0
    )
    mock_detector.generate_compliance_report.return_value = mock_report

    app.dependency_overrides[get_detector] = lambda: mock_detector

    response = client.get("/v1/compliance/test")

    assert response.status_code == 200
    data = response.json()
    assert data["compliance_score"] == 1.0

    # Reset overrides
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_clear_violations() -> None:
    """Test clear violations endpoint."""
    # Mock detector
    mock_detector = AsyncMock(spec=ViolationDetector)
    mock_detector.clear_history.return_value = 5

    app.dependency_overrides[get_detector] = lambda: mock_detector

    response = client.delete("/v1/violations/test")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cleared"
    assert data["count"] == 5

    # Reset overrides
    app.dependency_overrides = {}
