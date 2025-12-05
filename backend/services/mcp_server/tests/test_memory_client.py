"""
Tests for Memory Client
========================

Scientific tests for Episodic Memory service client.

Follows CODE_CONSTITUTION: ≥85% coverage, clear test names.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from clients.memory_client import MemoryClient


class TestMemoryClientBasics:
    """Test basic memory client functionality."""

    def test_client_creation(self, config):
        """HYPOTHESIS: MemoryClient initializes with config."""
        client = MemoryClient(config)
        assert client.config == config
        assert client.client is not None

    def test_client_uses_memory_url(self, config):
        """HYPOTHESIS: Client uses memory_url from config."""
        config.memory_url = "http://custom-memory:9000"
        client = MemoryClient(config)
        assert client.client.base_url == "http://custom-memory:9000"


class TestMemoryClientStore:
    """Test memory storage."""

    @pytest.mark.asyncio
    async def test_store_memory_success(self, config):
        """HYPOTHESIS: store() saves memory."""
        client = MemoryClient(config)

        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = {
                "id": "mem_123",
                "content": "Test memory",
                "memory_type": "experience"
            }

            result = await client.store(
                content="Test memory",
                memory_type="experience",
                importance=0.8
            )

            assert result["id"] == "mem_123"
            assert result["memory_type"] == "experience"
            mock_post.assert_called_once()

        await client.close()

    @pytest.mark.asyncio
    async def test_store_memory_with_tags(self, config):
        """HYPOTHESIS: store() accepts tags parameter."""
        client = MemoryClient(config)

        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = {"id": "mem_123"}

            await client.store(
                content="Tagged memory",
                memory_type="fact",
                tags=["important", "project_x"]
            )

            call_json = mock_post.call_args[1]["json"]
            assert "tags" in call_json
            assert call_json["tags"] == ["important", "project_x"]

        await client.close()


class TestMemoryClientSearch:
    """Test memory search."""

    @pytest.mark.asyncio
    async def test_search_memories_success(self, config):
        """HYPOTHESIS: search() finds relevant memories."""
        client = MemoryClient(config)

        with patch.object(client.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                "memories": [
                    {"id": "mem_1", "content": "First memory"},
                    {"id": "mem_2", "content": "Second memory"}
                ]
            }

            result = await client.search(query="test query", limit=10)

            assert len(result) == 2
            assert result[0]["id"] == "mem_1"
            mock_get.assert_called_once()

        await client.close()

    @pytest.mark.asyncio
    async def test_search_with_memory_type_filter(self, config):
        """HYPOTHESIS: search() filters by memory_type."""
        client = MemoryClient(config)

        with patch.object(client.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"memories": []}

            await client.search(
                query="test",
                memory_type="experience",
                limit=5
            )

            call_params = mock_get.call_args[1]["params"]
            assert call_params["memory_type"] == "experience"

        await client.close()


class TestMemoryClientConsolidate:
    """Test memory consolidation."""

    @pytest.mark.asyncio
    async def test_consolidate_success(self, config):
        """HYPOTHESIS: consolidate_to_vault() moves memories to vault."""
        client = MemoryClient(config)

        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = {
                "experience": 15,
                "semantic": 5
            }

            result = await client.consolidate_to_vault(threshold=0.8)

            assert result["experience"] == 15
            mock_post.assert_called_once()

        await client.close()


class TestMemoryClientContext:
    """Test context retrieval."""

    @pytest.mark.asyncio
    async def test_get_context_for_task_success(self, config):
        """HYPOTHESIS: get_context_for_task() returns context."""
        client = MemoryClient(config)

        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = {
                "episodic": [{"content": "Past event"}],
                "semantic": [{"content": "Known fact"}],
                "procedural": []
            }

            result = await client.get_context_for_task("write tests")

            assert "episodic" in result
            assert "semantic" in result
            mock_post.assert_called_once()

        await client.close()


class TestMemoryClientStats:
    """Test stats retrieval."""

    @pytest.mark.asyncio
    async def test_get_stats_success(self, config):
        """HYPOTHESIS: get_stats() returns memory statistics."""
        client = MemoryClient(config)

        with patch.object(client.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                "total": 100,
                "by_type": {"experience": 50, "semantic": 30, "procedural": 20}
            }

            result = await client.get_stats()

            assert result["total"] == 100
            mock_get.assert_called_once()

        await client.close()


class TestMemoryClientLifecycle:
    """Test client lifecycle management."""

    @pytest.mark.asyncio
    async def test_close_client(self, config):
        """HYPOTHESIS: close() releases resources."""
        client = MemoryClient(config)

        with patch.object(client.client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()
