"""
Maximus Core Service - API Routes
=================================

FastAPI endpoints for system coordination and health.
"""

from __future__ import annotations


from typing import List

from fastapi import APIRouter, Depends

from maximus_core_service.core.coordinator import SystemCoordinator
from maximus_core_service.core.health_aggregator import HealthAggregator
from maximus_core_service.models.system import SystemStatus
from maximus_core_service.api.dependencies import get_coordinator, get_health_aggregator

# FLORESCIMENTO: Introspection API
from maximus_core_service.consciousness.florescimento import florescimento_router

router = APIRouter()
router.include_router(florescimento_router)

@router.get("/health", response_model=dict)
async def health_check() -> dict[str, str]:
    """
    Service health check.

    Returns:
        Basic health status
    """
    return {"status": "healthy", "service": "maximus-core-service"}


@router.get("/system/status", response_model=SystemStatus)
async def get_system_status(
    aggregator: HealthAggregator = Depends(get_health_aggregator)
) -> SystemStatus:
    """
    Get aggregated system health status.

    Args:
        aggregator: Health aggregator instance

    Returns:
        System status with all service healths
    """
    return await aggregator.get_system_status()


@router.get("/services", response_model=List[str])
async def get_registered_services(
    coordinator: SystemCoordinator = Depends(get_coordinator)
) -> List[str]:
    """
    Get list of registered services.

    Args:
        coordinator: System coordinator instance

    Returns:
        List of registered service names
    """
    return list(coordinator.get_registered_services())


@router.post("/services/{service_name}/register", response_model=dict)
async def register_service(
    service_name: str,
    coordinator: SystemCoordinator = Depends(get_coordinator)
) -> dict[str, str]:
    """
    Register a service with the coordinator.

    Args:
        service_name: Name of service to register
        coordinator: System coordinator instance

    Returns:
        Registration confirmation
    """
    await coordinator.register_service(service_name)
    return {"status": "registered", "service": service_name}


@router.delete("/services/{service_name}", response_model=dict)
async def unregister_service(
    service_name: str,
    coordinator: SystemCoordinator = Depends(get_coordinator)
) -> dict[str, str]:
    """
    Unregister a service from the coordinator.

    Args:
        service_name: Name of service to unregister
        coordinator: System coordinator instance

    Returns:
        Unregistration confirmation
    """
    await coordinator.unregister_service(service_name)
    return {"status": "unregistered", "service": service_name}
