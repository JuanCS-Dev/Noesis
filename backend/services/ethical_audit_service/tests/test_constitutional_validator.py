"""
Unit tests for ConstitutionalValidator.
"""

from __future__ import annotations


import pytest

from config import AuditSettings
from core.constitutional_validator import (
    ConstitutionalValidator
)
from models.audit import ViolationType


@pytest.fixture(name="settings")
def fixture_settings() -> AuditSettings:
    """Audit settings fixture."""
    return AuditSettings(enable_blocking=False, max_violations_per_hour=100)


@pytest.fixture(name="validator")
def fixture_validator(settings: AuditSettings) -> ConstitutionalValidator:
    """Constitutional validator fixture."""
    return ConstitutionalValidator(settings)


@pytest.mark.asyncio
async def test_validate_clean_operation(validator: ConstitutionalValidator) -> None:
    """Test validating a clean operation."""
    is_valid, violations = await validator.validate_operation(
        service="test-service",
        operation="test-op",
        payload={"data": "clean"}
    )

    assert is_valid is True
    assert len(violations) == 0


@pytest.mark.asyncio
async def test_detect_placeholder_code(validator: ConstitutionalValidator) -> None:
    """Test detecting placeholder code."""
    is_valid, violations = await validator.validate_operation(
        service="test-service",
        operation="test-op",
        payload={"comment": "TODO: implement this"}
    )

    assert is_valid is False
    assert len(violations) > 0
    assert violations[0].violation_type == ViolationType.PLACEHOLDER_CODE


@pytest.mark.asyncio
async def test_detect_fake_success(validator: ConstitutionalValidator) -> None:
    """Test detecting fake success messages."""
    is_valid, violations = await validator.validate_operation(
        service="test-service",
        operation="test-op",
        payload={"status": "success", "error": "Failed actually"}
    )

    assert is_valid is False
    assert len(violations) > 0
    assert violations[0].violation_type == ViolationType.FAKE_SUCCESS


@pytest.mark.asyncio
async def test_detect_silent_modification(validator: ConstitutionalValidator) -> None:
    """Test detecting silent modifications."""
    is_valid, violations = await validator.validate_operation(
        service="test-service",
        operation="test-op",
        payload={"modified": True}
    )

    assert is_valid is False
    assert len(violations) > 0
    assert violations[0].violation_type == ViolationType.SILENT_MODIFICATION
