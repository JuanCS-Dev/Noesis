"""
Unit tests for Kubernetes Controller.
"""

from unittest.mock import AsyncMock
import pytest
from backend.services.hcl_executor_service.core.k8s import KubernetesController
from backend.services.hcl_executor_service.config import K8sSettings

@pytest.fixture(name="mock_settings")
def fixture_mock_settings() -> K8sSettings:
    """Mock settings fixture."""
    return K8sSettings(
        KUBE_CONFIG_PATH="/tmp/kubeconfig",
        KUBE_CONTEXT="test-context",
        KUBE_DEFAULT_NAMESPACE="default"
    )

@pytest.mark.asyncio
async def test_k8s_initialization(mock_settings: K8sSettings) -> None:
    """Test K8s controller initialization."""
    controller = KubernetesController(mock_settings)
    assert controller.settings == mock_settings
    assert controller.k8s_client is not None

@pytest.mark.asyncio
async def test_scale_deployment(mock_settings: K8sSettings) -> None:
    """Test scaling deployment."""
    controller = KubernetesController(mock_settings)

    # Mock the internal client
    controller.k8s_client.scale_deployment = AsyncMock(return_value=True) # type: ignore

    success = await controller.scale_deployment("maximus-core", "default", 3)
    assert success is True

    # Verify internal state of mock client
    controller.k8s_client.scale_deployment.assert_called_once_with("maximus-core", "default", 3)

@pytest.mark.asyncio
async def test_update_resource_limits(mock_settings: K8sSettings) -> None:
    """Test updating resource limits."""
    controller = KubernetesController(mock_settings)

    success = await controller.update_resource_limits(
        "maximus-core", "default", "2000m", "2Gi"
    )
    assert success is True

    deployment = await controller.k8s_client.get_deployment("maximus-core", "default")
    assert deployment is not None
    assert deployment["cpu_limit"] == "2000m"
    assert deployment["memory_limit"] == "2Gi"

@pytest.mark.asyncio
async def test_restart_pod(mock_settings: K8sSettings) -> None:
    """Test restarting pod."""
    controller = KubernetesController(mock_settings)

    success = await controller.restart_pod("maximus-core-pod-abc", "default")
    assert success is True

    # Verify internal state
    # Note: Mock client doesn't expose pods directly easily without get_cluster_info or similar
    # But we can check return value
