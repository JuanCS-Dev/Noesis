"""
Unit tests for HealthAggregator.
"""

from __future__ import annotations


import pytest

from backend.services.maximus_core_service.core.health_aggregator import (
    HealthAggregator
)


@pytest.fixture(name="aggregator")
def fixture_aggregator() -> HealthAggregator:
    """Health aggregator fixture."""
    return HealthAggregator()


@pytest.mark.asyncio
async def test_update_service_health(aggregator: HealthAggregator) -> None:
    """Test updating service health."""
    await aggregator.update_service_health("test-service", "healthy")

    status = await aggregator.get_system_status()
    assert "test-service" in status.services
    assert status.services["test-service"].status == "healthy"


@pytest.mark.asyncio
async def test_system_status_all_healthy(aggregator: HealthAggregator) -> None:
    """Test system status when all services are healthy."""
    await aggregator.update_service_health("service-1", "healthy")
    await aggregator.update_service_health("service-2", "healthy")

    status = await aggregator.get_system_status()
    assert status.status == "healthy"
    assert status.total_services == 2
    assert status.healthy_services == 2


@pytest.mark.asyncio
async def test_system_status_degraded(aggregator: HealthAggregator) -> None:
    """Test system status when some services are unhealthy."""
    await aggregator.update_service_health("service-1", "healthy")
    await aggregator.update_service_health("service-2", "unhealthy")

    status = await aggregator.get_system_status()
    assert status.status == "degraded"
    assert status.total_services == 2
    assert status.healthy_services == 1


@pytest.mark.asyncio
async def test_system_status_unhealthy(aggregator: HealthAggregator) -> None:
    """Test system status when all services are unhealthy."""
    await aggregator.update_service_health("service-1", "unhealthy")
    await aggregator.update_service_health("service-2", "unhealthy")

    status = await aggregator.get_system_status()
    assert status.status == "unhealthy"
    assert status.total_services == 2
    assert status.healthy_services == 0


@pytest.mark.asyncio
async def test_health_with_details(aggregator: HealthAggregator) -> None:
    """Test health update with details."""
    details = {"reason": "high_cpu", "value": "90%"}
    await aggregator.update_service_health(
        "test-service",
        "degraded",
        details
    )

    status = await aggregator.get_system_status()
    assert status.services["test-service"].details == details
