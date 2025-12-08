"""
Tests for storage backends to achieve 100% coverage.
"""

from __future__ import annotations


import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from metacognitive_reflector.core.punishment.storage_backends import (
    InMemoryBackend,
    RedisBackend,
    HAS_REDIS,
)
from metacognitive_reflector.core.punishment.models import (
    PenalRecord,
    PenalStatus,
    OffenseType,
)


class TestInMemoryBackend:
    """Tests for InMemoryBackend."""

    @pytest.mark.asyncio
    async def test_get_set(self):
        """Test basic get/set operations."""
        backend = InMemoryBackend()

        record = PenalRecord(
            agent_id="agent_001",
            status=PenalStatus.WARNING,
            offense=OffenseType.TRUTH_VIOLATION,
            offense_details="Test violation",
            until=datetime.now() + timedelta(hours=1),
        )

        await backend.set(record)
        retrieved = await backend.get("agent_001")

        assert retrieved is not None
        assert retrieved.agent_id == "agent_001"

    @pytest.mark.asyncio
    async def test_get_not_found(self):
        """Test get returns None for missing."""
        backend = InMemoryBackend()
        result = await backend.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_expired_auto_clear(self):
        """Test get auto-clears expired records."""
        backend = InMemoryBackend()

        # Create expired record
        record = PenalRecord(
            agent_id="agent_001",
            status=PenalStatus.WARNING,
            offense=OffenseType.TRUTH_VIOLATION,
            offense_details="Test",
            until=datetime.now() - timedelta(hours=1),  # Already expired
        )

        # Manually store without going through set
        backend._records["agent_001"] = record

        # Get should clear expired
        result = await backend.get("agent_001")
        assert result is None
        assert "agent_001" not in backend._records

    @pytest.mark.asyncio
    async def test_delete_exists(self):
        """Test delete existing record."""
        backend = InMemoryBackend()

        record = PenalRecord(
            agent_id="agent_001",
            status=PenalStatus.WARNING,
            offense=OffenseType.TRUTH_VIOLATION,
            offense_details="Test",
            until=datetime.now() + timedelta(hours=1),
        )

        await backend.set(record)
        result = await backend.delete("agent_001")

        assert result is True
        assert await backend.get("agent_001") is None

    @pytest.mark.asyncio
    async def test_delete_not_found(self):
        """Test delete non-existent record."""
        backend = InMemoryBackend()
        result = await backend.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_list_active(self):
        """Test list_active returns only active records."""
        backend = InMemoryBackend()

        # Active record
        record1 = PenalRecord(
            agent_id="agent_001",
            status=PenalStatus.WARNING,
            offense=OffenseType.TRUTH_VIOLATION,
            offense_details="Test",
            until=datetime.now() + timedelta(hours=1),
        )
        await backend.set(record1)

        # Another active
        record2 = PenalRecord(
            agent_id="agent_002",
            status=PenalStatus.PROBATION,
            offense=OffenseType.WISDOM_VIOLATION,
            offense_details="Test 2",
            until=datetime.now() + timedelta(hours=2),
        )
        await backend.set(record2)

        active = await backend.list_active()
        assert len(active) == 2

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health_check returns status."""
        backend = InMemoryBackend()
        health = await backend.health_check()

        assert health["healthy"] is True
        assert health["backend"] == "in_memory"
        assert "record_count" in health


class TestRedisBackend:
    """Tests for RedisBackend."""

    @pytest.mark.asyncio
    async def test_key_generation(self):
        """Test _key generates proper keys."""
        backend = RedisBackend()
        key = backend._key("agent_001")
        assert key == "maximus:penal:agent_001"

    @pytest.mark.asyncio
    async def test_get_client_no_redis(self):
        """Test _get_client raises without redis package."""
        # This test is covered by test_get_client_import_error below
        # which properly patches HAS_REDIS at module level
        pass

    @pytest.mark.asyncio
    async def test_get_client_import_error(self):
        """Test _get_client raises ImportError without redis."""
        backend = RedisBackend()

        # Patch HAS_REDIS at module level
        import metacognitive_reflector.core.punishment.storage_backends as storage_module

        original = storage_module.HAS_REDIS
        storage_module.HAS_REDIS = False

        try:
            with pytest.raises(ImportError, match="redis package required"):
                await backend._get_client()
        finally:
            storage_module.HAS_REDIS = original
            backend._client = None

    @pytest.mark.asyncio
    async def test_get_record_not_found(self):
        """Test get returns None when not found."""
        backend = RedisBackend()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=None)
        backend._client = mock_client

        result = await backend.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_record_found(self):
        """Test get returns record when found."""
        backend = RedisBackend()

        record = PenalRecord(
            agent_id="agent_001",
            status=PenalStatus.WARNING,
            offense=OffenseType.TRUTH_VIOLATION,
            offense_details="Test",
            until=datetime.now() + timedelta(hours=1),
        )

        import json
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=json.dumps(record.to_dict()))
        backend._client = mock_client

        result = await backend.get("agent_001")

        assert result is not None
        assert result.agent_id == "agent_001"

    @pytest.mark.asyncio
    async def test_get_expired_deletes(self):
        """Test get deletes expired records."""
        backend = RedisBackend()

        record = PenalRecord(
            agent_id="agent_001",
            status=PenalStatus.WARNING,
            offense=OffenseType.TRUTH_VIOLATION,
            offense_details="Test",
            until=datetime.now() - timedelta(hours=1),  # Expired
        )

        import json
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=json.dumps(record.to_dict()))
        mock_client.delete = AsyncMock()
        mock_client.srem = AsyncMock()
        backend._client = mock_client

        result = await backend.get("agent_001")

        assert result is None
        mock_client.delete.assert_called()

    @pytest.mark.asyncio
    async def test_set_with_ttl(self):
        """Test set stores with TTL."""
        backend = RedisBackend()

        record = PenalRecord(
            agent_id="agent_001",
            status=PenalStatus.WARNING,
            offense=OffenseType.TRUTH_VIOLATION,
            offense_details="Test",
            until=datetime.now() + timedelta(hours=1),
        )

        mock_client = AsyncMock()
        mock_client.setex = AsyncMock()
        mock_client.sadd = AsyncMock()
        backend._client = mock_client

        result = await backend.set(record)

        assert result is True
        mock_client.setex.assert_called_once()
        mock_client.sadd.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_without_until(self):
        """Test set uses default TTL when no until."""
        backend = RedisBackend(default_ttl=3600)

        record = PenalRecord(
            agent_id="agent_001",
            status=PenalStatus.WARNING,
            offense=OffenseType.TRUTH_VIOLATION,
            offense_details="Test",
            until=None,
        )

        mock_client = AsyncMock()
        mock_client.setex = AsyncMock()
        mock_client.sadd = AsyncMock()
        backend._client = mock_client

        await backend.set(record)

        # Should use default TTL
        call_args = mock_client.setex.call_args
        assert call_args[0][1] == 3600

    @pytest.mark.asyncio
    async def test_delete(self):
        """Test delete removes from Redis."""
        backend = RedisBackend()

        mock_client = AsyncMock()
        mock_client.delete = AsyncMock()
        mock_client.srem = AsyncMock()
        backend._client = mock_client

        result = await backend.delete("agent_001")

        assert result is True
        mock_client.delete.assert_called_once()
        mock_client.srem.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_active(self):
        """Test list_active retrieves all active records."""
        backend = RedisBackend()

        record1 = PenalRecord(
            agent_id="agent_001",
            status=PenalStatus.WARNING,
            offense=OffenseType.TRUTH_VIOLATION,
            offense_details="Test",
            until=datetime.now() + timedelta(hours=1),
        )
        record2 = PenalRecord(
            agent_id="agent_002",
            status=PenalStatus.PROBATION,
            offense=OffenseType.WISDOM_VIOLATION,
            offense_details="Test 2",
            until=datetime.now() + timedelta(hours=2),
        )

        import json
        mock_client = AsyncMock()
        mock_client.smembers = AsyncMock(return_value={"agent_001", "agent_002"})
        mock_client.get = AsyncMock(side_effect=[
            json.dumps(record1.to_dict()),
            json.dumps(record2.to_dict()),
        ])
        backend._client = mock_client

        records = await backend.list_active()

        assert len(records) == 2

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test health_check when Redis is healthy."""
        backend = RedisBackend()

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        backend._client = mock_client

        health = await backend.health_check()

        assert health["healthy"] is True
        assert health["backend"] == "redis"

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health_check when Redis fails."""
        backend = RedisBackend()

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(side_effect=ConnectionError("Failed"))
        backend._client = mock_client

        health = await backend.health_check()

        assert health["healthy"] is False
        assert "error" in health

    @pytest.mark.asyncio
    async def test_get_client_creates_connection(self):
        """Test _get_client creates Redis connection."""
        backend = RedisBackend(redis_url="redis://localhost:6379")

        # Skip if redis not installed
        if not HAS_REDIS:
            pytest.skip("redis package not installed")

        # Mock aioredis.from_url
        import metacognitive_reflector.core.punishment.storage_backends as storage_module

        mock_from_url = AsyncMock()
        mock_client = AsyncMock()
        mock_from_url.return_value = mock_client

        with patch.object(storage_module, 'aioredis') as mock_aioredis:
            mock_aioredis.from_url = mock_from_url

            result = await backend._get_client()

            # Should create client
            assert backend._client is not None
