"""
Unit tests for RequestRouter.
"""

from __future__ import annotations


import pytest

from backend.services.digital_thalamus_service.config import GatewaySettings
from backend.services.digital_thalamus_service.core.router import RequestRouter
from backend.services.digital_thalamus_service.models.gateway import RouteConfig


@pytest.fixture(name="settings")
def fixture_settings() -> GatewaySettings:
    """Gateway settings fixture."""
    return GatewaySettings(request_timeout=30.0, max_retries=3)


@pytest.fixture(name="router")
def fixture_router(settings: GatewaySettings) -> RequestRouter:
    """Router fixture."""
    return RequestRouter(settings)


@pytest.mark.asyncio
async def test_find_route_exact_match(router: RequestRouter) -> None:
    """Test finding route with exact match."""
    route = await router.find_route("/v1/core")
    assert route is not None
    assert route.service_name == "maximus-core-service"


@pytest.mark.asyncio
async def test_find_route_prefix_match(router: RequestRouter) -> None:
    """Test finding route with prefix matching."""
    route = await router.find_route("/v1/hcl/planner/some/path")
    assert route is not None
    assert route.service_name == "hcl-planner-service"


@pytest.mark.asyncio
async def test_find_route_no_match(router: RequestRouter) -> None:
    """Test finding route with no match."""
    route = await router.find_route("/nonexistent")
    assert route is None


@pytest.mark.asyncio
async def test_register_route(router: RequestRouter) -> None:
    """Test registering a new route."""
    new_route = RouteConfig(
        service_name="test-service",
        base_url="http://test:8000",
        timeout=10.0
    )
    await router.register_route("/v1/test", new_route)

    found_route = await router.find_route("/v1/test")
    assert found_route is not None
    assert found_route.service_name == "test-service"
