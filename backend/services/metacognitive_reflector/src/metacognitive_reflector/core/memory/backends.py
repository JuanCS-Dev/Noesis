"""
NOESIS Memory Fortress - Backend Operations
============================================

Redis (L2) and HTTP (L3) backend implementations.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import MemoryEntry, MemoryType, SearchResult

logger = logging.getLogger(__name__)


class RedisBackendMixin:
    """Mixin for Redis (L2) operations."""

    _redis_client: Optional[Any]
    _redis_url: Optional[str]

    async def _get_redis_client(self) -> Any:
        """Lazy initialize Redis client."""
        if self._redis_client is None and self._redis_url:
            try:
                import redis.asyncio as aioredis
                self._redis_client = await aioredis.from_url(
                    self._redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
            except ImportError:
                pass
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
        return self._redis_client

    async def _store_redis(self, entry: MemoryEntry) -> None:
        """Store in Redis (L2)."""
        client = await self._get_redis_client()
        if not client:
            raise ConnectionError("Redis client not available")

        key = f"noesis:memory:{entry.memory_id}"
        data = {
            "memory_id": entry.memory_id,
            "content": entry.content,
            "type": entry.memory_type.value,
            "importance": entry.importance,
            "context": entry.context,
            "timestamp": entry.timestamp.isoformat(),
        }
        await client.set(key, json.dumps(data), ex=604800)
        await client.sadd(f"noesis:memory:type:{entry.memory_type.value}", entry.memory_id)

    async def _get_redis(self, memory_id: str) -> Optional[MemoryEntry]:
        """Get from Redis (L2)."""
        client = await self._get_redis_client()
        if not client:
            raise ConnectionError("Redis client not available")

        key = f"noesis:memory:{memory_id}"
        data = await client.get(key)
        if not data:
            return None

        m = json.loads(data)
        return MemoryEntry(
            memory_id=m["memory_id"],
            content=m["content"],
            memory_type=MemoryType(m["type"]),
            importance=m.get("importance", 0.5),
            context=m.get("context", {}),
            timestamp=datetime.fromisoformat(m.get("timestamp", datetime.now().isoformat())),
        )

    async def _delete_redis(self, memory_id: str) -> bool:
        """Delete from Redis (L2)."""
        client = await self._get_redis_client()
        if not client:
            raise ConnectionError("Redis client not available")

        key = f"noesis:memory:{memory_id}"
        result = await client.delete(key)
        return result > 0


class HTTPBackendMixin:
    """Mixin for HTTP (L3) operations."""

    _http_client: Optional[Any]
    _base_url: Optional[str]
    _timeout: float

    async def _get_http_client(self) -> Any:
        """Lazy initialize HTTP client."""
        if self._http_client is None and self._base_url:
            try:
                import httpx
                self._http_client = httpx.AsyncClient(
                    base_url=self._base_url,
                    timeout=self._timeout,
                )
            except ImportError:
                pass
        return self._http_client

    async def _store_http(
        self,
        content: str,
        memory_type: MemoryType,
        importance: float,
        context: Optional[Dict[str, Any]],
    ) -> MemoryEntry:
        """Store via HTTP API (L3)."""
        client = await self._get_http_client()
        if not client:
            raise ConnectionError("HTTP client not available")

        response = await client.post(
            "/memories",
            json={
                "content": content,
                "type": memory_type.value,
                "importance": importance,
                "context": context or {},
            },
        )
        response.raise_for_status()

        data = response.json()
        return MemoryEntry(
            memory_id=data["memory_id"],
            content=content,
            memory_type=memory_type,
            importance=importance,
            context=context or {},
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
        )

    async def _search_http(
        self,
        query: str,
        memory_types: Optional[List[MemoryType]],
        limit: int,
        min_importance: float,
    ) -> SearchResult:
        """Search via HTTP API (L3)."""
        client = await self._get_http_client()
        if not client:
            raise ConnectionError("HTTP client not available")

        params: Dict[str, Any] = {
            "query": query,
            "limit": limit,
            "min_importance": min_importance,
        }
        if memory_types:
            params["types"] = ",".join(t.value for t in memory_types)

        response = await client.get("/memories/search", params=params)
        response.raise_for_status()

        data = response.json()
        memories = [
            MemoryEntry(
                memory_id=m["memory_id"],
                content=m["content"],
                memory_type=MemoryType(m["type"]),
                importance=m.get("importance", 0.5),
                context=m.get("context", {}),
                timestamp=datetime.fromisoformat(m.get("timestamp", datetime.now().isoformat())),
            )
            for m in data.get("memories", [])
        ]

        return SearchResult(
            memories=memories,
            total_found=data.get("total_found", len(memories)),
            query_time_ms=data.get("query_time_ms", 0.0),
        )

    async def _get_http(self, memory_id: str) -> Optional[MemoryEntry]:
        """Get via HTTP API (L3)."""
        client = await self._get_http_client()
        if not client:
            raise ConnectionError("HTTP client not available")

        response = await client.get(f"/memories/{memory_id}")
        if response.status_code == 404:
            return None

        response.raise_for_status()
        data = response.json()

        return MemoryEntry(
            memory_id=data["memory_id"],
            content=data["content"],
            memory_type=MemoryType(data["type"]),
            importance=data.get("importance", 0.5),
            context=data.get("context", {}),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
        )

    async def _delete_http(self, memory_id: str) -> bool:
        """Delete via HTTP API (L3)."""
        client = await self._get_http_client()
        if not client:
            raise ConnectionError("HTTP client not available")

        response = await client.delete(f"/memories/{memory_id}")
        return response.status_code == 200

