"""
Unit tests for Episodic Memory API.

Follows CODE_CONSTITUTION: 100% type hints, Google style.
"""

from __future__ import annotations

from typing import Any, Dict

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from httpx import Response

from api.routes import app, store

client: TestClient = TestClient(app)


def test_health_check() -> None:
    """Test health check endpoint."""
    response: Response = client.get("/health")
    assert response.status_code == 200
    data: Dict[str, Any] = response.json()
    assert data["status"] == "healthy"


def test_store_memory() -> None:
    """Test storing a memory."""
    payload: Dict[str, Any] = {
        "content": "API test memory",
        "type": "semantic",  # MIRIX type (not legacy "fact")
        "context": {"test": True}
    }
    response: Response = client.post("/v1/memories", json=payload)
    assert response.status_code == 200
    data: Dict[str, Any] = response.json()
    assert data["content"] == "API test memory"
    assert "memory_id" in data


def test_search_memories() -> None:
    """Test searching memories."""
    # First store a memory
    client.post("/v1/memories", json={
        "content": "Searchable memory",
        "type": "semantic"  # MIRIX type
    })

    # Then search
    payload: Dict[str, Any] = {
        "query_text": "searchable",
        "limit": 5
    }
    response: Response = client.post("/v1/memories/search", json=payload)
    assert response.status_code == 200
    data: Dict[str, Any] = response.json()
    assert data["total_found"] >= 1
    assert data["memories"][0]["content"] == "Searchable memory"


def test_get_and_delete_memory() -> None:
    """Test getting and deleting a memory."""
    # Store
    response: Response = client.post("/v1/memories", json={
        "content": "To delete",
        "type": "episodic"  # MIRIX type
    })
    memory_id: str = response.json()["memory_id"]

    # Get
    response = client.get(f"/v1/memories/{memory_id}")
    assert response.status_code == 200
    assert response.json()["content"] == "To delete"

    # Delete
    response = client.delete(f"/v1/memories/{memory_id}")
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Verify deleted
    response = client.get(f"/v1/memories/{memory_id}")
    assert response.status_code == 404


def test_consolidate_memories() -> None:
    """Test consolidate endpoint."""
    response: Response = client.post("/v1/memories/consolidate", json={
        "threshold": 0.8,
        "min_age_days": 7,
        "min_access_count": 2
    })
    assert response.status_code == 200
    data: Dict[str, Any] = response.json()
    assert data["success"] is True
    assert "consolidated" in data


def test_apply_decay() -> None:
    """Test decay endpoint."""
    response: Response = client.post("/v1/memories/decay", json={
        "decay_factor": 0.995,
        "boost_recent_access": True,
        "delete_threshold": 0.05
    })
    assert response.status_code == 200
    data: Dict[str, Any] = response.json()
    assert data["success"] is True
    assert "stats" in data


def test_get_task_context() -> None:
    """Test context endpoint."""
    # Store a memory first
    client.post("/v1/memories", json={
        "content": "Context test memory",
        "type": "semantic"
    })

    response: Response = client.post("/v1/memories/context", json={
        "task": "context test"
    })
    assert response.status_code == 200
    data: Dict[str, Any] = response.json()
    assert "task" in data
    assert "total_memories" in data


def test_get_stats() -> None:
    """Test stats endpoint."""
    response: Response = client.get("/v1/memories/stats")
    assert response.status_code == 200
    data: Dict[str, Any] = response.json()
    assert data["success"] is True
    assert "stats" in data


def test_get_memory_not_found() -> None:
    """Test get memory returns 404 for non-existent ID."""
    response: Response = client.get("/v1/memories/non-existent-id-12345")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_delete_memory_not_found() -> None:
    """Test delete memory returns 404 for non-existent ID."""
    response: Response = client.delete("/v1/memories/non-existent-id-12345")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_store_memory_invalid_type() -> None:
    """Test store memory with invalid type returns 422."""
    payload: Dict[str, Any] = {
        "content": "Test memory",
        "type": "invalid_type"
    }
    response: Response = client.post("/v1/memories", json=payload)
    assert response.status_code == 422


def test_consolidate_with_defaults() -> None:
    """Test consolidate endpoint with default parameters."""
    response: Response = client.post("/v1/memories/consolidate", json={})
    assert response.status_code == 200
    data: Dict[str, Any] = response.json()
    assert data["success"] is True


def test_decay_with_defaults() -> None:
    """Test decay endpoint with default parameters."""
    response: Response = client.post("/v1/memories/decay", json={})
    assert response.status_code == 200
    data: Dict[str, Any] = response.json()
    assert data["success"] is True


def test_context_empty_task() -> None:
    """Test context endpoint with empty result."""
    response: Response = client.post("/v1/memories/context", json={
        "task": "xyz123nonexistent"
    })
    assert response.status_code == 200
    data: Dict[str, Any] = response.json()
    assert data["total_memories"] == 0


# === Exception Handler Tests ===


def test_store_memory_exception() -> None:
    """Test store memory handles exceptions."""
    with patch.object(store, 'store', new_callable=AsyncMock) as mock_store:
        mock_store.side_effect = Exception("Database error")
        response: Response = client.post("/v1/memories", json={
            "content": "Test",
            "type": "semantic"
        })
        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]


def test_search_memories_exception() -> None:
    """Test search handles exceptions."""
    with patch.object(store, 'retrieve', new_callable=AsyncMock) as mock_retrieve:
        mock_retrieve.side_effect = Exception("Search failed")
        response: Response = client.post("/v1/memories/search", json={
            "query_text": "test",
            "limit": 5
        })
        assert response.status_code == 500
        assert "Search failed" in response.json()["detail"]


def test_get_stats_exception() -> None:
    """Test stats handles exceptions."""
    with patch.object(store, 'get_stats', new_callable=AsyncMock) as mock_stats:
        mock_stats.side_effect = Exception("Stats error")
        response: Response = client.get("/v1/memories/stats")
        assert response.status_code == 500
        assert "Stats error" in response.json()["detail"]


def test_consolidate_exception() -> None:
    """Test consolidate handles exceptions."""
    with patch.object(
        store, 'consolidate_to_vault', new_callable=AsyncMock
    ) as mock_consolidate:
        mock_consolidate.side_effect = Exception("Consolidation error")
        response: Response = client.post("/v1/memories/consolidate", json={})
        assert response.status_code == 500
        assert "Consolidation error" in response.json()["detail"]


def test_decay_exception() -> None:
    """Test decay handles exceptions."""
    with patch.object(
        store, 'decay_importance', new_callable=AsyncMock
    ) as mock_decay:
        mock_decay.side_effect = Exception("Decay error")
        response: Response = client.post("/v1/memories/decay", json={})
        assert response.status_code == 500
        assert "Decay error" in response.json()["detail"]


def test_context_exception() -> None:
    """Test context handles exceptions."""
    with patch('api.routes.ContextBuilder') as mock_builder_class:
        mock_builder: AsyncMock = AsyncMock()
        mock_builder.get_context_for_task.side_effect = Exception("Context error")
        mock_builder_class.return_value = mock_builder
        response: Response = client.post("/v1/memories/context", json={
            "task": "test task"
        })
        assert response.status_code == 500
        assert "Context error" in response.json()["detail"]
