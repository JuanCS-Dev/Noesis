"""
NOESIS Memory Fortress - L1 Hot Cache
======================================

In-Memory LRU Cache for fastest tier access.

Based on:
- LRU (Least Recently Used) eviction
- TTL-based expiration
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional

__all__ = ["L1HotCache"]


class L1HotCache:
    """
    L1 Hot Cache - In-Memory LRU Cache.

    Fastest tier (<1ms) for frequently accessed memories.
    Uses LRU eviction and TTL-based expiration.

    Usage:
        cache = L1HotCache(max_size=1000, ttl_seconds=300)
        await cache.set("key", {"data": "value"})
        data = await cache.get("key")
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 300,
    ) -> None:
        """
        Initialize hot cache.

        Args:
            max_size: Maximum entries
            ttl_seconds: Time-to-live for entries
        """
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._cache: Dict[str, Any] = {}
        self._access_order: List[str] = []
        self._timestamps: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        async with self._lock:
            if key not in self._cache:
                return None

            if self._is_expired(key):
                self._remove(key)
                return None

            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)

            return self._cache[key]

    async def set(self, key: str, value: Any) -> None:
        """
        Set item in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        async with self._lock:
            while len(self._cache) >= self._max_size:
                self._evict_oldest()

            self._cache[key] = value
            self._timestamps[key] = time.time()

            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)

    async def delete(self, key: str) -> bool:
        """
        Delete item from cache.

        Args:
            key: Cache key

        Returns:
            True if item was deleted
        """
        async with self._lock:
            if key in self._cache:
                self._remove(key)
                return True
            return False

    def _is_expired(self, key: str) -> bool:
        """Check if entry is expired."""
        if key not in self._timestamps:
            return True
        return time.time() - self._timestamps[key] > self._ttl

    def _remove(self, key: str) -> None:
        """Remove entry from all data structures."""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
        if key in self._access_order:
            self._access_order.remove(key)

    def _evict_oldest(self) -> None:
        """Evict least recently used entry."""
        if self._access_order:
            oldest = self._access_order.pop(0)
            self._cache.pop(oldest, None)
            self._timestamps.pop(oldest, None)

    async def clear(self) -> None:
        """Clear all entries."""
        async with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self._timestamps.clear()

    def get_status(self) -> Dict[str, Any]:
        """Get cache status."""
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "ttl_seconds": self._ttl,
            "utilization": len(self._cache) / self._max_size if self._max_size > 0 else 0,
        }

