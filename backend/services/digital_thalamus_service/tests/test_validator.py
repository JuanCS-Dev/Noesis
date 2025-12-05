"""
Unit tests for RequestValidator.
"""

from __future__ import annotations


import pytest

from backend.services.digital_thalamus_service.core.validator import (
    RequestValidator
)
from backend.services.digital_thalamus_service.models.gateway import GatewayRequest


@pytest.fixture(name="validator")
def fixture_validator() -> RequestValidator:
    """Validator fixture."""
    return RequestValidator()


@pytest.mark.asyncio
async def test_validate_valid_request(validator: RequestValidator) -> None:
    """Test validating a valid request."""
    request = GatewayRequest(
        path="/v1/test",
        method="GET",
        headers={},
        body=None
    )
    result = await validator.validate_request(request)
    assert result is True


@pytest.mark.asyncio
async def test_validate_invalid_method(validator: RequestValidator) -> None:
    """Test validating request with invalid method."""
    request = GatewayRequest(
        path="/v1/test",
        method="INVALID",
        headers={},
        body=None
    )
    result = await validator.validate_request(request)
    assert result is False


@pytest.mark.asyncio
async def test_validate_invalid_path(validator: RequestValidator) -> None:
    """Test validating request with invalid path."""
    request = GatewayRequest(
        path="invalid-path",
        method="GET",
        headers={},
        body=None
    )
    result = await validator.validate_request(request)
    assert result is False


@pytest.mark.asyncio
async def test_sanitize_headers(validator: RequestValidator) -> None:
    """Test header sanitization."""
    headers = {
        "Content-Type": "application/json",
        "X-Forwarded-For": "malicious-ip",
        "Authorization": "Bearer token"
    }
    sanitized = await validator.sanitize_headers(headers)

    assert "Content-Type" in sanitized
    assert "Authorization" in sanitized
    assert "X-Forwarded-For" not in sanitized


@pytest.mark.asyncio
async def test_validate_body_valid(validator: RequestValidator) -> None:
    """Test validating valid body."""
    result = await validator.validate_body({"key": "value"})
    assert result is True


@pytest.mark.asyncio
async def test_validate_body_none(validator: RequestValidator) -> None:
    """Test validating None body."""
    result = await validator.validate_body(None)
    assert result is True


@pytest.mark.asyncio
async def test_validate_body_invalid(validator: RequestValidator) -> None:
    """Test validating invalid body."""
    result = await validator.validate_body("not a dict")  # type: ignore
    assert result is False
