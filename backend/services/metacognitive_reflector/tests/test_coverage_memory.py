"""
Tests for MemoryClient to achieve 100% coverage.
"""

from __future__ import annotations


import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from metacognitive_reflector.core.memory_client import MemoryClient
from metacognitive_reflector.core.memory_models import MemoryEntry, MemoryType, SearchResult
from metacognitive_reflector.models.reflection import MemoryUpdate, MemoryUpdateType


class TestMemoryClientFallback:
    """Tests for MemoryClient fallback operations."""

    @pytest.mark.asyncio
    async def test_store_fallback(self):
        """Test store uses fallback when no base_url."""
        client = MemoryClient()
        entry = await client.store(
            content="Test content",
            memory_type=MemoryType.SEMANTIC,
            importance=0.8,
            context={"test": True},
        )
        assert entry.content == "Test content"
        assert entry.memory_type == MemoryType.SEMANTIC
        assert entry.importance == 0.8
        assert entry.context["test"] is True

    @pytest.mark.asyncio
    async def test_search_fallback(self):
        """Test search uses fallback."""
        client = MemoryClient()

        # Store some entries
        await client.store("Hello world", MemoryType.EPISODIC)
        await client.store("Python programming", MemoryType.SEMANTIC)
        await client.store("Hello again", MemoryType.PROCEDURAL)

        # Search
        result = await client.search("Hello")
        assert result.total_found >= 2

    @pytest.mark.asyncio
    async def test_search_fallback_with_filters(self):
        """Test search with type and importance filters."""
        client = MemoryClient()

        await client.store("Semantic 1", MemoryType.SEMANTIC, importance=0.9)
        await client.store("Episodic 1", MemoryType.EPISODIC, importance=0.5)
        await client.store("Semantic 2", MemoryType.SEMANTIC, importance=0.3)

        # Filter by type
        result = await client.search(
            "1",
            memory_types=[MemoryType.SEMANTIC],
            min_importance=0.5
        )
        # Should only get Semantic 1 (importance >= 0.5)
        assert all(m.memory_type == MemoryType.SEMANTIC for m in result.memories)

    @pytest.mark.asyncio
    async def test_get_fallback(self):
        """Test get from fallback storage."""
        client = MemoryClient()

        entry = await client.store("Test", MemoryType.EPISODIC)
        retrieved = await client.get(entry.memory_id)

        assert retrieved is not None
        assert retrieved.content == "Test"

    @pytest.mark.asyncio
    async def test_get_not_found(self):
        """Test get returns None for missing ID."""
        client = MemoryClient()
        result = await client.get("nonexistent_id")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_fallback(self):
        """Test delete from fallback storage."""
        client = MemoryClient()

        entry = await client.store("Test", MemoryType.EPISODIC)
        deleted = await client.delete(entry.memory_id)

        assert deleted is True
        assert await client.get(entry.memory_id) is None

    @pytest.mark.asyncio
    async def test_delete_not_found(self):
        """Test delete returns False for missing ID."""
        client = MemoryClient()
        result = await client.delete("nonexistent_id")
        assert result is False

    @pytest.mark.asyncio
    async def test_apply_updates(self):
        """Test apply_updates stores memories."""
        client = MemoryClient()

        updates = [
            MemoryUpdate(
                content="New knowledge",
                update_type=MemoryUpdateType.NEW_KNOWLEDGE,
                confidence=0.9,
                context_tags=["test"],
            ),
            MemoryUpdate(
                content="Correction",
                update_type=MemoryUpdateType.CORRECTION,
                confidence=0.8,
                context_tags=["test"],
            ),
            MemoryUpdate(
                content="Pattern",
                update_type=MemoryUpdateType.PATTERN,
                confidence=0.7,
                context_tags=["test"],
            ),
        ]

        result = await client.apply_updates(updates)
        assert result["status"] == "success"
        assert result["updates_applied"] == 3

    @pytest.mark.asyncio
    async def test_store_reflection(self):
        """Test store_reflection creates reflection memory."""
        client = MemoryClient()

        entry = await client.store_reflection(
            agent_id="agent_001",
            reflection_type="metacognitive",
            content="I learned something new",
            verdict_data={"decision": "pass"},
        )

        assert entry.memory_type == MemoryType.REFLECTION
        assert entry.importance == 0.7
        assert entry.context["agent_id"] == "agent_001"

    @pytest.mark.asyncio
    async def test_get_agent_history(self):
        """Test get_agent_history filters by agent_id."""
        client = MemoryClient()

        await client.store_reflection("agent_001", "test", "Memory 1")
        await client.store_reflection("agent_002", "test", "Memory 2")
        await client.store_reflection("agent_001", "test", "Memory 3")

        history = await client.get_agent_history("agent_001", limit=10)
        # All should be for agent_001
        assert all(m.context.get("agent_id") == "agent_001" for m in history)

    @pytest.mark.asyncio
    async def test_health_check_fallback(self):
        """Test health_check with fallback only."""
        client = MemoryClient()
        health = await client.health_check()

        assert health["healthy"] is True
        assert health["http_available"] is False
        assert health["fallback_enabled"] is True

    @pytest.mark.asyncio
    async def test_close_no_client(self):
        """Test close when no HTTP client exists."""
        client = MemoryClient()
        await client.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_map_update_type_unknown(self):
        """Test _map_update_type with unknown type."""
        client = MemoryClient()
        # Unknown type should default to EPISODIC
        result = client._map_update_type("UNKNOWN_TYPE")
        assert result == MemoryType.EPISODIC


class TestMemoryClientHTTP:
    """Tests for MemoryClient HTTP operations."""

    @pytest.mark.asyncio
    async def test_get_http_client_no_httpx(self):
        """Test _get_http_client without httpx installed."""
        client = MemoryClient(base_url="http://localhost:8000")

        # Patch import to fail
        with patch.dict("sys.modules", {"httpx": None}):
            with patch("builtins.__import__", side_effect=ImportError):
                result = await client._get_http_client()
                # Should return None when import fails
                assert result is None or client._http_client is None

    @pytest.mark.asyncio
    async def test_store_http_fallback_on_connection_error(self):
        """Test store falls back on ConnectionError."""
        client = MemoryClient(base_url="http://localhost:9999", use_fallback=True)

        # Mock _store_http to raise ConnectionError
        async def mock_store_http(*args, **kwargs):
            raise ConnectionError("Connection refused")

        client._store_http = mock_store_http

        # Store should fallback
        entry = await client.store("Test", MemoryType.EPISODIC)
        assert entry is not None
        assert entry.content == "Test"

    @pytest.mark.asyncio
    async def test_store_http_no_fallback_raises(self):
        """Test store raises when fallback disabled."""
        client = MemoryClient(base_url="http://localhost:9999", use_fallback=False)

        # Mock _get_http_client to return None
        client._get_http_client = AsyncMock(return_value=None)

        with pytest.raises(ConnectionError):
            await client._store_http("Test", MemoryType.EPISODIC, 0.5, None)

    @pytest.mark.asyncio
    async def test_search_http_fallback_on_error(self):
        """Test search falls back on error."""
        client = MemoryClient(base_url="http://localhost:9999", use_fallback=True)

        # Mock _search_http to raise
        async def mock_search_http(*args, **kwargs):
            raise ConnectionError("Connection refused")

        client._search_http = mock_search_http

        # Store first for fallback
        await client._store_fallback("Test content", MemoryType.EPISODIC, 0.5, None)

        result = await client.search("Test")
        assert result is not None

    @pytest.mark.asyncio
    async def test_search_http_no_client(self):
        """Test _search_http raises with no client."""
        client = MemoryClient(base_url="http://localhost:9999")
        client._get_http_client = AsyncMock(return_value=None)

        with pytest.raises(ConnectionError):
            await client._search_http("query", None, 10, 0.0)

    @pytest.mark.asyncio
    async def test_get_http_no_client(self):
        """Test _get_http raises with no client."""
        client = MemoryClient(base_url="http://localhost:9999")
        client._get_http_client = AsyncMock(return_value=None)

        with pytest.raises(ConnectionError):
            await client._get_http("test_id")

    @pytest.mark.asyncio
    async def test_delete_http_no_client(self):
        """Test _delete_http raises with no client."""
        client = MemoryClient(base_url="http://localhost:9999")
        client._get_http_client = AsyncMock(return_value=None)

        with pytest.raises(ConnectionError):
            await client._delete_http("test_id")

    @pytest.mark.asyncio
    async def test_get_fallback_on_connection_error(self):
        """Test get falls back on ConnectionError."""
        client = MemoryClient(base_url="http://localhost:9999", use_fallback=True)

        # Mock _get_http to raise
        async def mock_get_http(*args, **kwargs):
            raise ConnectionError("Connection refused")

        client._get_http = mock_get_http

        # Store in fallback
        entry = await client._store_fallback("Test", MemoryType.EPISODIC, 0.5, None)

        # Should use fallback when HTTP fails
        result = await client.get(entry.memory_id)
        assert result is not None

    @pytest.mark.asyncio
    async def test_delete_fallback_on_error(self):
        """Test delete falls back on error."""
        client = MemoryClient(base_url="http://localhost:9999", use_fallback=True)

        # Mock _delete_http to raise
        async def mock_delete_http(*args, **kwargs):
            raise ConnectionError("Connection refused")

        client._delete_http = mock_delete_http

        # Store in fallback
        entry = await client._store_fallback("Test", MemoryType.EPISODIC, 0.5, None)

        # Should use fallback
        result = await client.delete(entry.memory_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_with_http(self):
        """Test health_check attempts HTTP."""
        client = MemoryClient(base_url="http://localhost:9999", use_fallback=True)

        # Mock _get_http_client to return None so HTTP is unavailable
        client._get_http_client = AsyncMock(return_value=None)

        health = await client.health_check()
        # HTTP should fail, but fallback keeps it healthy
        assert health["healthy"] is True
        assert health["http_available"] is False

    @pytest.mark.asyncio
    async def test_close_with_client(self):
        """Test close when HTTP client exists."""
        client = MemoryClient(base_url="http://localhost:9999")

        # Create mock client
        mock_http = AsyncMock()
        mock_http.aclose = AsyncMock()
        client._http_client = mock_http

        await client.close()

        mock_http.aclose.assert_called_once()
        assert client._http_client is None


class TestMemoryClientHTTPMocked:
    """Tests for HTTP methods with mocked responses."""

    @pytest.mark.asyncio
    async def test_store_http_success(self):
        """Test _store_http with successful response."""
        client = MemoryClient(base_url="http://localhost:8000")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "memory_id": "mem_123",
            "timestamp": datetime.now().isoformat(),
        }
        mock_response.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_response)
        client._get_http_client = AsyncMock(return_value=mock_http)

        entry = await client._store_http(
            "Test content",
            MemoryType.SEMANTIC,
            0.8,
            {"key": "value"},
        )

        assert entry.memory_id == "mem_123"
        assert entry.content == "Test content"

    @pytest.mark.asyncio
    async def test_search_http_success(self):
        """Test _search_http with successful response."""
        client = MemoryClient(base_url="http://localhost:8000")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "memories": [
                {
                    "memory_id": "mem_1",
                    "content": "Test 1",
                    "type": "semantic",
                    "importance": 0.5,
                    "context": {},
                    "timestamp": datetime.now().isoformat(),
                }
            ],
            "total_found": 1,
            "query_time_ms": 10.0,
        }
        mock_response.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        client._get_http_client = AsyncMock(return_value=mock_http)

        result = await client._search_http(
            "test",
            [MemoryType.SEMANTIC],
            10,
            0.0,
        )

        assert result.total_found == 1
        assert len(result.memories) == 1

    @pytest.mark.asyncio
    async def test_get_http_success(self):
        """Test _get_http with successful response."""
        client = MemoryClient(base_url="http://localhost:8000")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "memory_id": "mem_1",
            "content": "Test",
            "type": "semantic",
        }
        mock_response.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        client._get_http_client = AsyncMock(return_value=mock_http)

        result = await client._get_http("mem_1")

        assert result is not None
        assert result.memory_id == "mem_1"

    @pytest.mark.asyncio
    async def test_get_http_not_found(self):
        """Test _get_http returns None for 404."""
        client = MemoryClient(base_url="http://localhost:8000")

        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        client._get_http_client = AsyncMock(return_value=mock_http)

        result = await client._get_http("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_http_success(self):
        """Test _delete_http with successful response."""
        client = MemoryClient(base_url="http://localhost:8000")

        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_http = AsyncMock()
        mock_http.delete = AsyncMock(return_value=mock_response)
        client._get_http_client = AsyncMock(return_value=mock_http)

        result = await client._delete_http("mem_1")

        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_http_success(self):
        """Test health_check with successful HTTP."""
        client = MemoryClient(base_url="http://localhost:8000")

        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        client._get_http_client = AsyncMock(return_value=mock_http)

        health = await client.health_check()

        assert health["http_available"] is True
        assert health["healthy"] is True
