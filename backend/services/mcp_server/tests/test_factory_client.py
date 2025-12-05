"""
Tests for Factory Client
=========================

Scientific tests for Tool Factory service client.

Follows CODE_CONSTITUTION: ≥85% coverage, clear test names.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from clients.factory_client import FactoryClient


class TestFactoryClientBasics:
    """Test basic factory client functionality."""

    def test_client_creation(self, config):
        """HYPOTHESIS: FactoryClient initializes with config."""
        client = FactoryClient(config)
        assert client.config == config
        assert client.client is not None

    def test_client_uses_factory_url(self, config):
        """HYPOTHESIS: Client uses factory_url from config."""
        config.factory_url = "http://custom-factory:9000"
        client = FactoryClient(config)
        assert client.client.base_url == "http://custom-factory:9000"


class TestFactoryClientGenerate:
    """Test tool generation."""

    @pytest.mark.asyncio
    async def test_generate_tool_success(self, config):
        """HYPOTHESIS: generate_tool() creates new tool."""
        client = FactoryClient(config)

        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = {
                "name": "test_tool",
                "code": "def test_tool(): return 42",
                "success_rate": 1.0
            }

            result = await client.generate_tool(
                name="test_tool",
                description="A test tool",
                examples=[{"input": {}, "expected": 42}]
            )

            assert result["name"] == "test_tool"
            mock_post.assert_called_once()

        await client.close()

    @pytest.mark.asyncio
    async def test_generate_tool_with_examples(self, config):
        """HYPOTHESIS: generate_tool() accepts examples."""
        client = FactoryClient(config)

        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = {"name": "tool", "code": "pass"}

            await client.generate_tool(
                "double",
                "Doubles a number",
                [{"input": {"x": 2}, "expected": 4}]
            )

            call_args = mock_post.call_args
            assert "examples" in call_args[1]["json"]

        await client.close()


class TestFactoryClientExecute:
    """Test tool execution."""

    @pytest.mark.asyncio
    async def test_execute_tool_success(self, config):
        """HYPOTHESIS: execute_tool() runs tool with parameters."""
        client = FactoryClient(config)

        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = {
                "result": 42,
                "success": True,
                "execution_time": 0.05
            }

            result = await client.execute_tool("test_tool", {"x": 10})

            assert result["result"] == 42
            assert result["success"] is True
            mock_post.assert_called_once()

        await client.close()


class TestFactoryClientList:
    """Test tool listing."""

    @pytest.mark.asyncio
    async def test_list_tools_empty(self, config):
        """HYPOTHESIS: list_tools() returns empty list when no tools."""
        client = FactoryClient(config)

        with patch.object(client.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"tools": []}

            result = await client.list_tools()

            assert result == []
            mock_get.assert_called_once_with("/v1/tools")

        await client.close()

    @pytest.mark.asyncio
    async def test_list_tools_with_results(self, config):
        """HYPOTHESIS: list_tools() returns available tools."""
        client = FactoryClient(config)

        with patch.object(client.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                "tools": [
                    {"name": "tool1", "description": "First tool"},
                    {"name": "tool2", "description": "Second tool"}
                ]
            }

            result = await client.list_tools()

            assert len(result) == 2
            assert result[0]["name"] == "tool1"

        await client.close()


class TestFactoryClientDelete:
    """Test tool deletion."""

    @pytest.mark.asyncio
    async def test_delete_tool_success(self, config):
        """HYPOTHESIS: delete_tool() removes tool."""
        client = FactoryClient(config)

        with patch.object(client.client, 'delete', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = {"success": True}

            result = await client.delete_tool("test_tool")

            assert result is True
            mock_delete.assert_called_once()

        await client.close()


class TestFactoryClientGetTool:
    """Test getting single tool."""

    @pytest.mark.asyncio
    async def test_get_tool_success(self, config):
        """HYPOTHESIS: get_tool() returns tool specification."""
        client = FactoryClient(config)

        with patch.object(client.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                "name": "test_tool",
                "code": "def test_tool(): return 42",
                "description": "Test tool"
            }

            result = await client.get_tool("test_tool")

            assert result["name"] == "test_tool"
            assert "code" in result
            mock_get.assert_called_once()

        await client.close()


class TestFactoryClientLifecycle:
    """Test client lifecycle management."""

    @pytest.mark.asyncio
    async def test_close_client(self, config):
        """HYPOTHESIS: close() releases resources."""
        client = FactoryClient(config)

        with patch.object(client.client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()
