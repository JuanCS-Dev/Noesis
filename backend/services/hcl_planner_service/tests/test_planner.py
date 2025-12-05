"""
Unit tests for Agentic Planner.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from config import GeminiSettings
from core.planner import (
    AgenticPlanner,
    PlannerNotAvailableError,
)


@pytest.fixture(name="mock_settings")
def fixture_mock_settings():
    """Mock settings fixture."""
    return GeminiSettings(
        GEMINI_API_KEY="test-key",
        GEMINI_MODEL="gemini-3.0-pro-test",
        GEMINI_THINKING_LEVEL="high"
    )


@pytest.fixture(name="mock_gemini_client")
def fixture_mock_gemini_client():
    """Mock Gemini client fixture."""
    with patch("core.planner.GeminiClient") as mock:
        client_instance = AsyncMock()
        mock.return_value = client_instance
        yield client_instance


@pytest.mark.asyncio
async def test_planner_initialization_success(mock_settings, mock_gemini_client):
    """Test successful planner initialization."""
    planner = AgenticPlanner(mock_settings)
    assert planner.client is not None
    mock_gemini_client.assert_not_called()  # Constructor called, but instance is mock


@pytest.mark.asyncio
async def test_planner_initialization_no_key():
    """Test planner initialization without API key."""
    settings = GeminiSettings(GEMINI_API_KEY=None)
    planner = AgenticPlanner(settings)
    assert planner.client is None


@pytest.mark.asyncio
async def test_recommend_actions_success(mock_settings, mock_gemini_client):
    """Test successful action recommendation."""
    planner = AgenticPlanner(mock_settings)

    mock_gemini_client.generate_plan.return_value = {
        "actions": [{"type": "scale_up"}],
        "reasoning": "Test reasoning",
        "thought_trace": "Test trace"
    }

    actions = await planner.recommend_actions(
        current_state={"cpu": 0.9},
        analysis_result={"status": "critical"},
        operational_goals={"target": 0.7}
    )

    assert len(actions) == 1
    assert actions[0]["type"] == "scale_up"
    mock_gemini_client.generate_plan.assert_called_once()


@pytest.mark.asyncio
async def test_recommend_actions_disabled():
    """Test action recommendation when planner is disabled."""
    settings = GeminiSettings(GEMINI_API_KEY=None)
    planner = AgenticPlanner(settings)

    with pytest.raises(PlannerNotAvailableError):
        await planner.recommend_actions({}, {}, {})


@pytest.mark.asyncio
async def test_get_status_active(mock_settings, mock_gemini_client):  # pylint: disable=unused-argument
    """Test planner status when active."""
    planner = AgenticPlanner(mock_settings)
    # Mock client config access
    planner.client.config.model = "test-model"
    planner.client.config.thinking_level = "high"

    status = await planner.get_status()
    assert status["status"] == "active"
    assert status["model"] == "test-model"


@pytest.mark.asyncio
async def test_get_status_disabled():
    """Test planner status when disabled."""
    settings = GeminiSettings(GEMINI_API_KEY=None)
    planner = AgenticPlanner(settings)

    status = await planner.get_status()
    assert status["status"] == "disabled"
