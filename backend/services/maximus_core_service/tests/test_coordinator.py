"""
Unit tests for SystemCoordinator.
"""

from __future__ import annotations


import pytest

from backend.services.maximus_core_service.config import CoordinationSettings
from backend.services.maximus_core_service.core.coordinator import SystemCoordinator


@pytest.fixture(name="settings")
def fixture_settings() -> CoordinationSettings:
    """Coordination settings fixture."""
    return CoordinationSettings(
        health_check_interval=30.0,
        service_timeout=5.0
    )


@pytest.fixture(name="coordinator")
def fixture_coordinator(settings: CoordinationSettings) -> SystemCoordinator:
    """Coordinator fixture."""
    return SystemCoordinator(settings)


@pytest.mark.asyncio
async def test_register_service(coordinator: SystemCoordinator) -> None:
    """Test service registration."""
    await coordinator.register_service("test-service")

    services = coordinator.get_registered_services()
    assert "test-service" in services
    assert len(services) == 1


@pytest.mark.asyncio
async def test_register_duplicate_service(coordinator: SystemCoordinator) -> None:
    """Test that duplicate registration doesn't create duplicates."""
    await coordinator.register_service("test-service")
    await coordinator.register_service("test-service")

    services = coordinator.get_registered_services()
    assert services.count("test-service") == 1


@pytest.mark.asyncio
async def test_unregister_service(coordinator: SystemCoordinator) -> None:
    """Test service unregistration."""
    await coordinator.register_service("test-service")
    await coordinator.unregister_service("test-service")

    services = coordinator.get_registered_services()
    assert "test-service" not in services
    assert len(services) == 0


@pytest.mark.asyncio
async def test_get_registered_services(coordinator: SystemCoordinator) -> None:
    """Test getting registered services."""
    await coordinator.register_service("service-1")
    await coordinator.register_service("service-2")

    services = coordinator.get_registered_services()
    assert len(services) == 2
    assert "service-1" in services
    assert "service-2" in services
