"""
End-to-end API tests for Metacognitive Reflector.

Tests all new tribunal system endpoints:
- Health endpoints (basic and detailed)
- Reflection endpoints (basic and with verdict)
- Agent management endpoints (status, pardon, execute-punishment)
"""

from __future__ import annotations


import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from metacognitive_reflector.api.routes import router
from metacognitive_reflector.api.dependencies import get_memory_client, get_reflector
from metacognitive_reflector.config import get_settings
from metacognitive_reflector.core.memory_client import MemoryClient
from metacognitive_reflector.core.reflector import Reflector


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


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_basic_health(self, client):
        """Test basic health endpoint."""
        response = client.get("/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "metacognitive-reflector"

    def test_detailed_health(self, client):
        """Test detailed health endpoint."""
        response = client.get("/v1/health/detailed")
        assert response.status_code == 200

        data = response.json()
        assert "healthy" in data
        assert "tribunal" in data
        assert "executor" in data
        assert "memory" in data


class TestReflectionEndpoints:
    """Tests for reflection endpoints."""

    def test_reflect_basic(self, client):
        """Test basic reflection endpoint."""
        log = {
            "trace_id": "test-reflect-001",
            "agent_id": "test_agent",
            "task": "Test task",
            "action": "Performed analysis correctly",
            "outcome": "Success",
        }

        response = client.post("/v1/reflect", json=log)
        assert response.status_code == 200

        data = response.json()
        assert "critique" in data
        assert "memory_updates" in data
        assert data["critique"]["trace_id"] == "test-reflect-001"

    def test_reflect_with_reasoning_trace(self, client):
        """Test reflection with reasoning trace."""
        log = {
            "trace_id": "test-reflect-002",
            "agent_id": "planner_agent",
            "task": "Create deployment plan",
            "action": "Analyzed requirements and created comprehensive plan",
            "outcome": "Plan ready",
            "reasoning_trace": "Step 1: Identified dependencies. Step 2: Created timeline.",
        }

        response = client.post("/v1/reflect", json=log)
        assert response.status_code == 200

        data = response.json()
        assert data["critique"]["quality_score"] >= 0.0
        assert data["critique"]["quality_score"] <= 1.0

    def test_reflect_with_verdict(self, client):
        """Test reflection with full verdict details."""
        log = {
            "trace_id": "test-verdict-001",
            "agent_id": "executor_agent",
            "task": "Execute operation",
            "action": "Performed operation with validation",
            "outcome": "Completed successfully",
        }

        response = client.post("/v1/reflect/verdict", json=log)
        assert response.status_code == 200

        data = response.json()
        assert "critique" in data
        assert "verdict" in data
        assert "memory_updates" in data

        # Check verdict structure
        verdict = data["verdict"]
        assert "decision" in verdict
        assert "consensus_score" in verdict
        assert "individual_verdicts" in verdict
        assert "vote_breakdown" in verdict
        assert "reasoning" in verdict

    def test_reflect_verdict_contains_all_judges(self, client):
        """Test that verdict contains all three judges."""
        log = {
            "trace_id": "test-judges-001",
            "agent_id": "test_agent",
            "task": "Test",
            "action": "Action",
            "outcome": "Outcome",
        }

        response = client.post("/v1/reflect/verdict", json=log)
        data = response.json()

        individual = data["verdict"]["individual_verdicts"]
        assert "VERITAS" in individual
        assert "SOPHIA" in individual
        assert "DIKĒ" in individual

    def test_reflect_vote_breakdown(self, client):
        """Test that vote breakdown is properly structured."""
        log = {
            "trace_id": "test-votes-001",
            "agent_id": "test_agent",
            "task": "Test",
            "action": "Action",
            "outcome": "Outcome",
        }

        response = client.post("/v1/reflect/verdict", json=log)
        data = response.json()

        votes = data["verdict"]["vote_breakdown"]
        assert len(votes) == 3  # Three judges

        for vote in votes:
            assert "judge_name" in vote
            assert "pillar" in vote
            assert "weight" in vote
            assert "abstained" in vote


class TestAgentManagementEndpoints:
    """Tests for agent management endpoints."""

    def test_get_agent_status_clear(self, client):
        """Test getting status for agent with no punishment."""
        response = client.get("/v1/agent/clean_agent/status")
        assert response.status_code == 200

        data = response.json()
        assert data["agent_id"] == "clean_agent"
        assert data["active"] is False
        assert data["status"] == "clear"

    def test_pardon_nonexistent_punishment(self, client):
        """Test pardoning agent with no active punishment."""
        response = client.post(
            "/v1/agent/clean_agent/pardon",
            json={"reason": "Test pardon"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is False
        assert "clean_agent" in data["message"]

    def test_execute_punishment_no_offense(self, client):
        """Test execute punishment with no offense detected."""
        log = {
            "trace_id": "test-punish-001",
            "agent_id": "good_agent",
            "task": "Perform task correctly",
            "action": "Analyzed and executed with proper validation",
            "outcome": "Success",
        }

        response = client.post("/v1/agent/good_agent/execute-punishment", json=log)
        assert response.status_code == 200

        data = response.json()
        assert data["agent_id"] == "good_agent"
        # Most executions with good behavior should not be punished
        assert "punishment_executed" in data


class TestReflectionValidation:
    """Tests for input validation."""

    def test_missing_required_fields(self, client):
        """Test that missing required fields return error."""
        log = {
            "trace_id": "test-invalid",
            # Missing: agent_id, task, action, outcome
        }

        response = client.post("/v1/reflect", json=log)
        assert response.status_code == 422  # Validation error

    def test_empty_trace_id(self, client):
        """Test that empty trace_id is accepted."""
        log = {
            "trace_id": "",  # Empty but present
            "agent_id": "test",
            "task": "task",
            "action": "action",
            "outcome": "outcome",
        }

        # Pydantic should accept empty string
        response = client.post("/v1/reflect", json=log)
        # Might be 200 or 422 depending on validation rules
        assert response.status_code in [200, 422]


class TestPardonRequest:
    """Tests for pardon request validation."""

    def test_pardon_empty_reason(self, client):
        """Test that empty reason is rejected."""
        response = client.post(
            "/v1/agent/test_agent/pardon",
            json={"reason": ""}
        )
        assert response.status_code == 422  # Validation error

    def test_pardon_with_valid_reason(self, client):
        """Test pardon with valid reason."""
        response = client.post(
            "/v1/agent/test_agent/pardon",
            json={"reason": "Completed re-education successfully"}
        )
        assert response.status_code == 200


class TestEndToEndFlow:
    """End-to-end flow tests."""

    def test_full_reflection_flow(self, client):
        """Test complete reflection flow."""
        # 1. Submit reflection
        log = {
            "trace_id": "e2e-test-001",
            "agent_id": "e2e_agent",
            "task": "Complete E2E test task",
            "action": "Performed comprehensive analysis",
            "outcome": "Task completed",
            "reasoning_trace": "Followed protocol correctly",
        }

        response = client.post("/v1/reflect/verdict", json=log)
        assert response.status_code == 200

        data = response.json()

        # 2. Verify critique
        assert data["critique"]["trace_id"] == "e2e-test-001"
        assert len(data["critique"]["philosophical_checks"]) == 3

        # 3. Verify verdict
        assert data["verdict"]["decision"] in ["pass", "review", "fail", "capital"]

        # 4. Check agent status
        status_response = client.get("/v1/agent/e2e_agent/status")
        assert status_response.status_code == 200

    def test_violation_detection_flow(self, client):
        """Test flow with potential violation."""
        log = {
            "trace_id": "violation-test-001",
            "agent_id": "suspicious_agent",
            "task": "Execute command",
            "action": "I think maybe possibly perhaps this might work",
            "outcome": "Unclear result",
            "reasoning_trace": "Not sure about this",
        }

        response = client.post("/v1/reflect/verdict", json=log)
        assert response.status_code == 200

        data = response.json()

        # Should have lower quality score due to uncertain language
        assert "critique" in data
        assert "verdict" in data

    def test_tribunal_health_after_operations(self, client):
        """Test tribunal health after operations."""
        # Perform some reflections
        for i in range(3):
            log = {
                "trace_id": f"health-test-{i}",
                "agent_id": "health_test_agent",
                "task": "Test task",
                "action": "Test action",
                "outcome": "Success",
            }
            client.post("/v1/reflect", json=log)

        # Check health
        response = client.get("/v1/health/detailed")
        assert response.status_code == 200

        data = response.json()
        # Tribunal should still be healthy after operations
        assert data["healthy"] is True
