"""
Unit tests for Action Executor.
"""

from unittest.mock import AsyncMock
import pytest
from backend.services.hcl_executor_service.core.executor import ActionExecutor
from backend.services.hcl_executor_service.models.actions import Action, ActionParameters

@pytest.fixture(name="mock_k8s_controller")
def fixture_mock_k8s_controller() -> AsyncMock:
    """Mock K8s controller fixture."""
    return AsyncMock()

@pytest.mark.asyncio
async def test_execute_scale_deployment(mock_k8s_controller: AsyncMock) -> None:
    """Test scaling deployment action."""
    mock_k8s_controller.scale_deployment.return_value = True
    executor = ActionExecutor(mock_k8s_controller)

    action = Action(
        type="scale_deployment",
        parameters=ActionParameters(
            deployment_name="test-dep",
            namespace="default",
            replicas=3
        )
    )

    results = await executor.execute_actions("plan-1", [action])

    assert len(results) == 1
    assert results[0].status == "success"
    mock_k8s_controller.scale_deployment.assert_called_once_with(
        "test-dep", "default", 3
    )

@pytest.mark.asyncio
async def test_execute_update_limits(mock_k8s_controller: AsyncMock) -> None:
    """Test updating resource limits action."""
    mock_k8s_controller.update_resource_limits.return_value = True
    executor = ActionExecutor(mock_k8s_controller)

    action = Action(
        type="update_resource_limits",
        parameters=ActionParameters(
            deployment_name="test-dep",
            namespace="default",
            cpu_limit="100m",
            memory_limit="128Mi"
        )
    )

    results = await executor.execute_actions("plan-1", [action])

    assert len(results) == 1
    assert results[0].status == "success"
    mock_k8s_controller.update_resource_limits.assert_called_once_with(
        "test-dep", "default", "100m", "128Mi"
    )

@pytest.mark.asyncio
async def test_execute_restart_pod(mock_k8s_controller: AsyncMock) -> None:
    """Test restarting pod action."""
    mock_k8s_controller.restart_pod.return_value = True
    executor = ActionExecutor(mock_k8s_controller)

    action = Action(
        type="restart_pod",
        parameters=ActionParameters(
            pod_name="test-pod",
            namespace="default"
        )
    )

    results = await executor.execute_actions("plan-1", [action])

    assert len(results) == 1
    assert results[0].status == "success"
    mock_k8s_controller.restart_pod.assert_called_once_with(
        "test-pod", "default"
    )

@pytest.mark.asyncio
async def test_execute_unsupported_action(mock_k8s_controller: AsyncMock) -> None:
    """Test unsupported action."""
    executor = ActionExecutor(mock_k8s_controller)

    action = Action(
        type="unknown_action",
        parameters=ActionParameters()
    )

    results = await executor.execute_actions("plan-1", [action])

    assert len(results) == 1
    assert results[0].status == "failed"
    assert "Unsupported action type" in results[0].details

@pytest.mark.asyncio
async def test_execute_action_failure(mock_k8s_controller: AsyncMock) -> None:
    """Test action execution failure."""
    mock_k8s_controller.scale_deployment.side_effect = Exception("K8s error")
    executor = ActionExecutor(mock_k8s_controller)

    action = Action(
        type="scale_deployment",
        parameters=ActionParameters(
            deployment_name="test-dep",
            replicas=3
        )
    )

    results = await executor.execute_actions("plan-1", [action])

    assert len(results) == 1
    assert results[0].status == "failed"
    assert "K8s error" in results[0].details
