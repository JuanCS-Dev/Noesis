"""
Tests for API routes to achieve 100% coverage.
"""

from __future__ import annotations


import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from metacognitive_reflector.api.routes import router
from metacognitive_reflector.api.dependencies import get_reflector
from metacognitive_reflector.models.reflection import (
    OffenseLevel,
    ExecutionLog,
    Critique,
    PhilosophicalCheck,
)


# Create test app
app = FastAPI()
app.include_router(router, prefix="/v1")


class TestPardonEndpoint:
    """Tests for pardon endpoint edge cases."""

    @pytest.mark.asyncio
    async def test_pardon_success(self):
        """Test successful pardon."""
        mock_reflector = MagicMock()
        mock_reflector.pardon_agent = AsyncMock(return_value=True)

        app.dependency_overrides[get_reflector] = lambda: mock_reflector
        client = TestClient(app)

        response = client.post(
            "/v1/agent/agent_001/pardon",
            json={"reason": "Test pardon"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "pardoned" in data["message"]

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_pardon_no_punishment(self):
        """Test pardon when no active punishment."""
        mock_reflector = MagicMock()
        mock_reflector.pardon_agent = AsyncMock(return_value=False)

        app.dependency_overrides[get_reflector] = lambda: mock_reflector
        client = TestClient(app)

        response = client.post(
            "/v1/agent/agent_001/pardon",
            json={"reason": "Test pardon"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "No active punishment" in data["message"]

        app.dependency_overrides.clear()


class TestExecutePunishmentEndpoint:
    """Tests for execute-punishment endpoint edge cases."""

    @pytest.mark.asyncio
    async def test_execute_punishment_with_offense(self):
        """Test punishment execution with offense."""
        mock_reflector = MagicMock()

        # Mock critique
        mock_critique = Critique(
            trace_id="trace_001",
            quality_score=0.3,
            philosophical_checks=[
                PhilosophicalCheck(
                    pillar="Truth",
                    passed=False,
                    reasoning="Violation detected",
                )
            ],
            offense_level=OffenseLevel.MAJOR,
            critique_text="Major violation",
        )
        mock_reflector.analyze_log = AsyncMock(return_value=mock_critique)

        # Mock punishment outcome
        mock_outcome = MagicMock()
        mock_outcome.result.value = "success"
        mock_outcome.handler = "rollback_handler"
        mock_outcome.actions_taken = ["action1"]
        mock_outcome.message = "Punishment executed"
        mock_outcome.requires_followup = False

        mock_reflector.execute_punishment = AsyncMock(return_value=mock_outcome)

        app.dependency_overrides[get_reflector] = lambda: mock_reflector
        client = TestClient(app)

        response = client.post(
            "/v1/agent/agent_001/execute-punishment",
            json={
                "trace_id": "trace_001",
                "agent_id": "agent_001",
                "task": "Test task",
                "action": "Test action",
                "outcome": "Test outcome",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["punishment_executed"] is True

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_execute_punishment_no_offense(self):
        """Test punishment execution with no offense."""
        mock_reflector = MagicMock()

        # Mock critique with no offense
        mock_critique = Critique(
            trace_id="trace_001",
            quality_score=0.9,
            philosophical_checks=[
                PhilosophicalCheck(
                    pillar="Truth",
                    passed=True,
                    reasoning="All good",
                )
            ],
            offense_level=OffenseLevel.NONE,
            critique_text="No issues",
        )
        mock_reflector.analyze_log = AsyncMock(return_value=mock_critique)
        mock_reflector.execute_punishment = AsyncMock(return_value=None)

        app.dependency_overrides[get_reflector] = lambda: mock_reflector
        client = TestClient(app)

        response = client.post(
            "/v1/agent/agent_001/execute-punishment",
            json={
                "trace_id": "trace_002",
                "agent_id": "agent_001",
                "task": "Test task",
                "action": "Test action",
                "outcome": "Test outcome",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["punishment_executed"] is False
        assert "No offense detected" in data["reason"]

        app.dependency_overrides.clear()
