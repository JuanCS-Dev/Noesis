"""
Tests for Memory Tools
=======================

Scientific tests for Episodic Memory MCP tools.

Follows CODE_CONSTITUTION: ≥85% coverage, clear test names.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from tools.memory_tools import (
    memory_store,
    memory_search,
    memory_consolidate,
    memory_context,
)


class TestMemoryStoreTool:
    """Test memory_store MCP tool."""

    @pytest.mark.asyncio
    async def test_store_success(self):
        """HYPOTHESIS: memory_store() saves memory."""
        with patch("clients.memory_client.BaseHTTPClient") as MockHTTP:
            mock_http = AsyncMock()
            mock_http.post.return_value = {
                "id": "mem_123",
                "content": "Test memory",
                "memory_type": "experience"
            }
            mock_http.close.return_value = None
            MockHTTP.return_value = mock_http

            result = await memory_store(
                content="Test memory",
                memory_type="experience",
                importance=0.8
            )

            assert result["id"] == "mem_123"
            assert result["memory_type"] == "experience"

    @pytest.mark.asyncio
    async def test_store_validates_memory_type(self):
        """HYPOTHESIS: memory_store() validates memory_type."""
        with pytest.raises(Exception):
            await memory_store(
                content="Test",
                memory_type="invalid_type",
            )


class TestMemorySearchTool:
    """Test memory_search MCP tool."""

    @pytest.mark.asyncio
    async def test_search_success(self):
        """HYPOTHESIS: memory_search() finds relevant memories."""
        with patch("clients.memory_client.BaseHTTPClient") as MockHTTP:
            mock_http = AsyncMock()
            mock_http.get.return_value = {
                "memories": [
                    {"id": "mem_1", "content": "First"},
                    {"id": "mem_2", "content": "Second"}
                ]
            }
            mock_http.close.return_value = None
            MockHTTP.return_value = mock_http

            result = await memory_search(query="test query", limit=10)

            assert len(result) == 2


class TestMemoryConsolidateTool:
    """Test memory_consolidate MCP tool."""

    @pytest.mark.asyncio
    async def test_consolidate_success(self):
        """HYPOTHESIS: memory_consolidate() moves memories to vault."""
        with patch("clients.memory_client.BaseHTTPClient") as MockHTTP:
            mock_http = AsyncMock()
            mock_http.post.return_value = {
                "experience": 15,
                "fact": 10
            }
            mock_http.close.return_value = None
            MockHTTP.return_value = mock_http

            result = await memory_consolidate(threshold=0.8)

            assert result["experience"] == 15
            assert result["fact"] == 10


class TestMemoryContextTool:
    """Test memory_context MCP tool."""

    @pytest.mark.asyncio
    async def test_context_success(self):
        """HYPOTHESIS: memory_context() returns relevant context."""
        with patch("clients.memory_client.BaseHTTPClient") as MockHTTP:
            mock_http = AsyncMock()
            mock_http.post.return_value = {
                "experience": [{"id": "mem_1"}],
                "procedural": [{"id": "mem_2"}],
                "core": [{"id": "mem_3"}]
            }
            mock_http.close.return_value = None
            MockHTTP.return_value = mock_http

            result = await memory_context("write tests")

            assert "experience" in result
            assert "procedural" in result
            assert "core" in result
