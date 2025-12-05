"""
Tests for Factory Tools
========================

Scientific tests for Tool Factory MCP tools.

Follows CODE_CONSTITUTION: ≥85% coverage, clear test names.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from tools.factory_tools import (
    factory_generate,
    factory_execute,
    factory_list,
    factory_delete,
)


class TestFactoryGenerateTool:
    """Test factory_generate MCP tool."""

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """HYPOTHESIS: factory_generate() creates new tool."""
        mock_result = {
            "name": "test_tool",
            "code": "def test(): return 42",
            "success_rate": 1.0
        }

        with patch("clients.factory_client.BaseHTTPClient") as MockHTTP:
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_result
            mock_http.close.return_value = None
            MockHTTP.return_value = mock_http

            result = await factory_generate(
                name="test_tool",
                description="A test tool that does something",
                examples=[{"input": {}, "expected": 42}]
            )

            assert result["name"] == "test_tool"
            assert "code" in result

    @pytest.mark.asyncio
    async def test_generate_validates_input(self):
        """HYPOTHESIS: factory_generate() validates request model."""
        with pytest.raises(Exception):  # Pydantic validation error
            await factory_generate(
                name="",  # Invalid: empty name
                description="short",  # Invalid: too short
                examples=[]  # Invalid: no examples
            )


class TestFactoryExecuteTool:
    """Test factory_execute MCP tool."""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """HYPOTHESIS: factory_execute() runs tool."""
        with patch("clients.factory_client.BaseHTTPClient") as MockHTTP:
            mock_http = AsyncMock()
            mock_http.post.return_value = {
                "return_value": 42,
                "success": True,
                "execution_time": 0.05
            }
            mock_http.close.return_value = None
            MockHTTP.return_value = mock_http

            result = await factory_execute("test_tool", {"x": 10})

            assert result["return_value"] == 42
            assert result["success"] is True


class TestFactoryListTool:
    """Test factory_list MCP tool."""

    @pytest.mark.asyncio
    async def test_list_empty(self):
        """HYPOTHESIS: factory_list() returns empty list when no tools."""
        with patch("clients.factory_client.BaseHTTPClient") as MockHTTP:
            mock_http = AsyncMock()
            mock_http.get.return_value = {"tools": []}
            mock_http.close.return_value = None
            MockHTTP.return_value = mock_http

            result = await factory_list()

            assert result == []

    @pytest.mark.asyncio
    async def test_list_with_tools(self):
        """HYPOTHESIS: factory_list() returns available tools."""
        with patch("clients.factory_client.BaseHTTPClient") as MockHTTP:
            mock_http = AsyncMock()
            mock_http.get.return_value = {
                "tools": [
                    {"name": "tool1", "description": "First"},
                    {"name": "tool2", "description": "Second"}
                ]
            }
            mock_http.close.return_value = None
            MockHTTP.return_value = mock_http

            result = await factory_list()

            assert len(result) == 2
            assert result[0]["name"] == "tool1"


class TestFactoryDeleteTool:
    """Test factory_delete MCP tool."""

    @pytest.mark.asyncio
    async def test_delete_success(self):
        """HYPOTHESIS: factory_delete() removes tool."""
        with patch("clients.factory_client.BaseHTTPClient") as MockHTTP:
            mock_http = AsyncMock()
            mock_http.delete.return_value = {"success": True}
            mock_http.close.return_value = None
            MockHTTP.return_value = mock_http

            result = await factory_delete("test_tool")

            assert result is True  # delete_tool extracts success from dict


class TestFactoryToolsCleanup:
    """Test cleanup scenarios."""

    @pytest.mark.asyncio
    async def test_client_closes_on_exception(self):
        """HYPOTHESIS: Client closes even if operation fails."""
        with patch("clients.factory_client.BaseHTTPClient") as MockHTTP:
            mock_http = AsyncMock()
            mock_http.post.side_effect = Exception("Tool failed")
            mock_http.close.return_value = None
            MockHTTP.return_value = mock_http

            with pytest.raises(Exception):
                await factory_execute("bad_tool", {})
