"""
Test Fixtures for MCP Server.

Pytest fixtures for MCP Server tests.
Follows CODE_CONSTITUTION: 100% type hints, Google style.
"""

from __future__ import annotations

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock

import pytest

from config import MCPServerConfig


@pytest.fixture
def config() -> MCPServerConfig:
    """Create test configuration.

    Returns:
        MCPServerConfig with test defaults.
    """
    return MCPServerConfig(
        service_name="mcp-server-test",
        service_port=9999,
        log_level="DEBUG",
        tribunal_url="http://localhost:8101",
        factory_url="http://localhost:8105",
        memory_url="http://localhost:8103",
        rate_limit_per_tool=10,
        rate_limit_window=60,
        circuit_breaker_threshold=3,
        circuit_breaker_timeout=10.0,
        http_timeout=5.0,
    )


@pytest.fixture
def mock_tribunal_response() -> Dict[str, Any]:
    """Mock successful tribunal response.

    Returns:
        Dict with tribunal verdict.
    """
    return {
        "decision": "PASS",
        "consensus_score": 0.85,
        "verdicts": {
            "VERITAS": {"score": 0.9, "reasoning": "Truth verified"},
            "SOPHIA": {"score": 0.8, "reasoning": "Wisdom confirmed"},
            "DIKE": {"score": 0.85, "reasoning": "Justice satisfied"},
        },
        "punishment": None,
        "trace_id": "test-trace-123",
    }


@pytest.fixture
def mock_factory_response() -> Dict[str, Any]:
    """Mock successful factory response.

    Returns:
        Dict with ToolSpec.
    """
    return {
        "name": "test_tool",
        "description": "Test tool",
        "parameters": {"x": {"type": "int", "required": "True"}},
        "return_type": "int",
        "code": "def test_tool(x: int) -> int:\n    return x * 2",
        "examples": [{"input": {"x": 2}, "expected": 4}],
        "success_rate": 1.0,
    }


@pytest.fixture
def mock_memory_response() -> Dict[str, Any]:
    """Mock successful memory response.

    Returns:
        Dict with memory metadata.
    """
    return {
        "id": "mem_12345",
        "content": "Test memory",
        "memory_type": "experience",
        "importance": 0.8,
        "tags": ["test"],
        "timestamp": "2025-12-04T10:00:00Z",
    }


@pytest.fixture
def mock_httpx_response() -> MagicMock:
    """Mock httpx Response.

    Returns:
        Mock response object.
    """
    response: MagicMock = MagicMock()
    response.status_code = 200
    response.json = MagicMock(return_value={"status": "ok"})
    response.raise_for_status = MagicMock()
    return response


@pytest.fixture
async def mock_async_client(mock_httpx_response: MagicMock) -> AsyncMock:
    """Mock httpx AsyncClient.

    Args:
        mock_httpx_response: Mock HTTP response fixture.

    Returns:
        AsyncMock client.
    """
    client: AsyncMock = AsyncMock()
    client.get = AsyncMock(return_value=mock_httpx_response)
    client.post = AsyncMock(return_value=mock_httpx_response)
    client.delete = AsyncMock(return_value=mock_httpx_response)
    client.aclose = AsyncMock()
    return client
