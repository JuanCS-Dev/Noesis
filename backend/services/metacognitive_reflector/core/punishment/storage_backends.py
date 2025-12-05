"""
MAXIMUS 2.0 - Penal Registry Storage Backends
==============================================

Storage backend implementations for punishment persistence.
Extracted from penal_registry.py for CODE_CONSTITUTION compliance (< 500 lines).

Contains:
- StorageBackend: Abstract base class
- InMemoryBackend: For testing/development
- RedisBackend: Production storage
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

try:
    import redis.asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

if TYPE_CHECKING:
    from .penal_registry import PenalRecord


class StorageBackend(ABC):
    """
    Abstract storage backend for penal records.

    Implementations must provide:
    - get: Retrieve a record by agent_id
    - set: Store a record
    - delete: Remove a record
    - list_active: List all active punishments
    - health_check: Check backend health
    """

    @abstractmethod
    async def get(self, agent_id: str) -> Optional["PenalRecord"]:
        """
        Get penal record for agent.

        Args:
            agent_id: Agent identifier

        Returns:
            PenalRecord if found, None otherwise
        """

    @abstractmethod
    async def set(self, record: "PenalRecord") -> bool:
        """
        Store penal record.

        Args:
            record: Record to store

        Returns:
            True if stored successfully
        """

    @abstractmethod
    async def delete(self, agent_id: str) -> bool:
        """
        Delete penal record.

        Args:
            agent_id: Agent identifier

        Returns:
            True if deleted, False if not found
        """

    @abstractmethod
    async def list_active(self) -> List["PenalRecord"]:
        """
        List all active punishments.

        Returns:
            List of active PenalRecord instances
        """

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check backend health.

        Returns:
            Health status dictionary
        """


class InMemoryBackend(StorageBackend):
    """
    In-memory storage backend for testing/development.

    Not persistent across restarts. Use for:
    - Unit tests
    - Development
    - Fallback when Redis unavailable
    """

    def __init__(self) -> None:
        """Initialize empty storage."""
        # pylint: disable=import-outside-toplevel
        from .penal_registry import PenalRecord
        self._record_class = PenalRecord
        self._records: Dict[str, "PenalRecord"] = {}

    async def get(self, agent_id: str) -> Optional["PenalRecord"]:
        """Get penal record, auto-clearing expired."""
        record = self._records.get(agent_id)
        if record and not record.is_active:
            # Auto-clear expired records
            del self._records[agent_id]
            return None
        return record

    async def set(self, record: "PenalRecord") -> bool:
        """Store penal record."""
        self._records[record.agent_id] = record
        return True

    async def delete(self, agent_id: str) -> bool:
        """Delete penal record."""
        if agent_id in self._records:
            del self._records[agent_id]
            return True
        return False

    async def list_active(self) -> List["PenalRecord"]:
        """List all active punishments."""
        return [r for r in self._records.values() if r.is_active]

    async def health_check(self) -> Dict[str, Any]:
        """Check backend health."""
        return {
            "healthy": True,
            "backend": "in_memory",
            "record_count": len(self._records),
        }


class RedisBackend(StorageBackend):
    """
    Redis storage backend for production use.

    Features:
    - TTL-based expiration
    - Index for listing active punishments
    - Connection pooling via aioredis

    Requires:
        pip install redis
    """

    KEY_PREFIX = "maximus:penal:"
    INDEX_KEY = "maximus:penal:index"

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_ttl: int = 86400 * 7,  # 7 days
    ) -> None:
        """
        Initialize Redis backend.

        Args:
            redis_url: Redis connection URL
            default_ttl: Default TTL in seconds (7 days)
        """
        # pylint: disable=import-outside-toplevel
        from .penal_registry import PenalRecord
        self._record_class = PenalRecord
        self._redis_url = redis_url
        self._default_ttl = default_ttl
        self._client: Optional[Any] = None

    async def _get_client(self) -> Any:
        """Lazy initialize Redis client."""
        if self._client is None:
            if not HAS_REDIS:
                raise ImportError(
                    "redis package required. Install with: pip install redis"
                )
            self._client = await aioredis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._client

    def _key(self, agent_id: str) -> str:
        """Generate Redis key for agent."""
        return f"{self.KEY_PREFIX}{agent_id}"

    async def get(self, agent_id: str) -> Optional["PenalRecord"]:
        """Get penal record from Redis."""
        client = await self._get_client()
        data = await client.get(self._key(agent_id))
        if not data:
            return None

        record = self._record_class.from_dict(json.loads(data))
        if not record.is_active:
            await self.delete(agent_id)
            return None
        return record

    async def set(self, record: "PenalRecord") -> bool:
        """Store penal record in Redis with TTL."""
        client = await self._get_client()
        key = self._key(record.agent_id)
        data = json.dumps(record.to_dict())

        # Calculate TTL
        if record.until:
            ttl = int((record.until - datetime.now()).total_seconds())
            ttl = max(60, ttl)  # Minimum 60 seconds
        else:
            ttl = self._default_ttl

        # Store record with TTL
        await client.setex(key, ttl, data)

        # Add to index
        await client.sadd(self.INDEX_KEY, record.agent_id)

        return True

    async def delete(self, agent_id: str) -> bool:
        """Delete penal record from Redis."""
        client = await self._get_client()
        await client.delete(self._key(agent_id))
        await client.srem(self.INDEX_KEY, agent_id)
        return True

    async def list_active(self) -> List["PenalRecord"]:
        """List all active punishments from Redis."""
        client = await self._get_client()
        agent_ids = await client.smembers(self.INDEX_KEY)

        records = []
        for agent_id in agent_ids:
            record = await self.get(agent_id)
            if record:
                records.append(record)

        return records

    async def health_check(self) -> Dict[str, Any]:
        """Check Redis health."""
        try:
            client = await self._get_client()
            await client.ping()
            return {
                "healthy": True,
                "backend": "redis",
                "url": self._redis_url,
            }
        except (ConnectionError, TimeoutError, OSError) as e:
            return {
                "healthy": False,
                "backend": "redis",
                "error": str(e),
            }
