"""
Metacognitive Reflector - Unit Tests
====================================

Tests for core Reflector logic with the new tribunal system.
"""

from __future__ import annotations


import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from metacognitive_reflector.config import get_settings
from metacognitive_reflector.api.routes import router
from metacognitive_reflector.api.dependencies import get_memory_client, get_reflector
from metacognitive_reflector.core.memory_client import MemoryClient
from metacognitive_reflector.core.reflector import Reflector
from metacognitive_reflector.models.reflection import ExecutionLog, OffenseLevel


# Create test app
app = FastAPI()
app.include_router(router, prefix="/v1")


@pytest.fixture
def settings():
    """Get test settings."""
    return get_settings()


@pytest.fixture
def reflector(settings):
    """Create Reflector instance."""
    return Reflector(settings)


@pytest.fixture
def memory_client():
    """Create MemoryClient instance."""
    return MemoryClient()


@pytest.fixture
def client(reflector, memory_client):
    """Create test client with dependency overrides."""
    app.dependency_overrides[get_reflector] = lambda: reflector
    app.dependency_overrides[get_memory_client] = lambda: memory_client
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestHealthEndpoint:
    """Tests for health endpoint."""

    def test_health_check(self, client):
        """Test health returns healthy status."""
        response = client.get("/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestReflectionEndpoint:
    """Tests for reflection endpoint."""

    def test_reflection_success(self, client):
        """Test successful reflection with no violations."""
        log = {
            "trace_id": "test-success-001",
            "agent_id": "hcl_planner",
            "task": "Plan deployment",
            "action": "Generated deployment plan with proper analysis",
            "outcome": "Plan created successfully",
            "reasoning_trace": "Analyzed requirements and created steps.",
        }

        response = client.post("/v1/reflect", json=log)
        assert response.status_code == 200

        data = response.json()
        assert "critique" in data
        assert "memory_updates" in data
        assert data["critique"]["trace_id"] == "test-success-001"

    def test_reflection_with_execution_log(self, client):
        """Test reflection processes execution log correctly."""
        log = {
            "trace_id": "test-log-002",
            "agent_id": "executor_agent",
            "task": "Execute task",
            "action": "Performed the requested operation",
            "outcome": "Operation completed",
        }

        response = client.post("/v1/reflect", json=log)
        assert response.status_code == 200

        data = response.json()
        assert data["critique"]["quality_score"] >= 0.0
        assert data["critique"]["quality_score"] <= 1.0


class TestReflectorCore:
    """Tests for Reflector core logic."""

    @pytest.mark.asyncio
    async def test_analyze_log_returns_critique(self, reflector):
        """Test analyze_log returns a Critique."""
        log = ExecutionLog(
            trace_id="core-test-001",
            agent_id="test_agent",
            task="Test task",
            action="Test action",
            outcome="Test outcome",
        )

        critique = await reflector.analyze_log(log)

        assert critique.trace_id == "core-test-001"
        assert critique.quality_score >= 0.0
        assert critique.quality_score <= 1.0
        assert len(critique.philosophical_checks) == 3  # VERITAS, SOPHIA, DIKĒ

    @pytest.mark.asyncio
    async def test_generate_memory_updates(self, reflector):
        """Test memory update generation."""
        log = ExecutionLog(
            trace_id="memory-test-001",
            agent_id="test_agent",
            task="Test",
            action="Action",
            outcome="Success",
        )

        critique = await reflector.analyze_log(log)
        updates = await reflector.generate_memory_updates(critique)

        assert len(updates) >= 1

    @pytest.mark.asyncio
    async def test_apply_punishment_none(self, reflector):
        """Test no punishment for no offense."""
        result = await reflector.apply_punishment(OffenseLevel.NONE)
        assert result is None

    @pytest.mark.asyncio
    async def test_apply_punishment_minor(self, reflector):
        """Test punishment for minor offense."""
        result = await reflector.apply_punishment(OffenseLevel.MINOR)
        assert result == "RE_EDUCATION_LOOP"

    @pytest.mark.asyncio
    async def test_apply_punishment_major(self, reflector):
        """Test punishment for major offense."""
        result = await reflector.apply_punishment(OffenseLevel.MAJOR)
        assert result == "ROLLBACK_AND_PROBATION"

    @pytest.mark.asyncio
    async def test_apply_punishment_capital(self, reflector):
        """Test punishment for capital offense."""
        result = await reflector.apply_punishment(OffenseLevel.CAPITAL)
        assert result == "DELETION_REQUEST"

    @pytest.mark.asyncio
    async def test_health_check(self, reflector):
        """Test reflector health check."""
        health = await reflector.health_check()

        assert "healthy" in health
        assert "tribunal" in health
        assert "executor" in health
        assert "memory" in health


class TestReflectorWithTribunal:
    """Tests for Reflector with full tribunal integration."""

    @pytest.mark.asyncio
    async def test_tribunal_deliberation(self, reflector):
        """Test full tribunal deliberation."""
        log = ExecutionLog(
            trace_id="tribunal-test-001",
            agent_id="planner_agent",
            task="Create plan",
            action="Analyzed and created comprehensive plan",
            outcome="Plan ready for execution",
            reasoning_trace="Considered all factors and dependencies.",
        )

        critique, verdict = await reflector.analyze_with_verdict(log)

        # Check critique
        assert critique.trace_id == "tribunal-test-001"
        assert len(critique.philosophical_checks) == 3

        # Check verdict has all judges
        assert "VERITAS" in verdict.individual_verdicts
        assert "SOPHIA" in verdict.individual_verdicts
        assert "DIKĒ" in verdict.individual_verdicts

    @pytest.mark.asyncio
    async def test_store_reflection(self, reflector):
        """Test storing reflection in memory."""
        log = ExecutionLog(
            trace_id="store-test-001",
            agent_id="test_agent",
            task="Test",
            action="Action",
            outcome="Success",
        )

        critique = await reflector.analyze_log(log)

        # Should not raise
        await reflector.store_reflection(
            agent_id="test_agent",
            critique=critique,
        )

    @pytest.mark.asyncio
    async def test_check_agent_status(self, reflector):
        """Test checking agent punishment status."""
        status = await reflector.check_agent_status("nonexistent_agent")

        assert status["active"] is False
        assert status["status"] == "clear"
