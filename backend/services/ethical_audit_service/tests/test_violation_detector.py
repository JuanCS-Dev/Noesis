"""
Unit tests for ViolationDetector.
"""

from __future__ import annotations


import pytest

from config import AuditSettings
from core.violation_detector import (
    ViolationDetector
)
from models.audit import (
    Violation,
    ViolationSeverity,
    ViolationType
)


@pytest.fixture(name="settings")
def fixture_settings() -> AuditSettings:
    """Audit settings fixture."""
    return AuditSettings(enable_blocking=False, max_violations_per_hour=100)


@pytest.fixture(name="detector")
def fixture_detector(settings: AuditSettings) -> ViolationDetector:
    """Violation detector fixture."""
    return ViolationDetector(settings)


@pytest.mark.asyncio
async def test_record_violation(detector: ViolationDetector) -> None:
    """Test recording a violation."""
    violation = Violation(
        violation_id="test-violation",
        violation_type=ViolationType.PLACEHOLDER_CODE,
        severity=ViolationSeverity.HIGH,
        description="Test violation",
        service="test-service"
    )

    await detector.record_violation(violation)

    assert len(detector.violation_history) == 1
    assert detector.violation_history[0].violation_id == "test-violation"


@pytest.mark.asyncio
async def test_generate_compliance_report(detector: ViolationDetector) -> None:
    """Test generating compliance report."""
    violation = Violation(
        violation_id="test-v1",
        violation_type=ViolationType.FAKE_SUCCESS,
        severity=ViolationSeverity.CRITICAL,
        description="Test violation",
        service="test-service"
    )

    await detector.record_violation(violation)

    report = await detector.generate_compliance_report("test-service", 10)

    assert report.total_checks == 10
    assert report.passed_checks == 9
    assert len(report.violations) == 1
    assert report.compliance_score == 0.9


@pytest.mark.asyncio
async def test_clear_history_specific_service(detector: ViolationDetector) -> None:
    """Test clearing history for specific service."""
    v1 = Violation(
        violation_id="v1",
        violation_type=ViolationType.PLACEHOLDER_CODE,
        severity=ViolationSeverity.HIGH,
        description="Test",
        service="service-1"
    )
    v2 = Violation(
        violation_id="v2",
        violation_type=ViolationType.FAKE_SUCCESS,
        severity=ViolationSeverity.CRITICAL,
        description="Test",
        service="service-2"
    )

    await detector.record_violation(v1)
    await detector.record_violation(v2)

    count = await detector.clear_history("service-1")

    assert count == 1
    assert len(detector.violation_history) == 1
    assert detector.violation_history[0].service == "service-2"


@pytest.mark.asyncio
async def test_clear_all_history(detector: ViolationDetector) -> None:
    """Test clearing all history."""
    for i in range(3):
        violation = Violation(
            violation_id=f"v{i}",
            violation_type=ViolationType.PLACEHOLDER_CODE,
            severity=ViolationSeverity.HIGH,
            description="Test",
            service=f"service-{i}"
        )
        await detector.record_violation(violation)

    count = await detector.clear_history()

    assert count == 3
    assert len(detector.violation_history) == 0
