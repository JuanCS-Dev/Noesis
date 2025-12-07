"""LRU Cache for Inference Results.

Thread-safe LRU cache implementation.
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import Any


class LRUCache:
    """LRU (Least Recently Used) cache for inference results.

    Attributes:
        cache: Ordered dictionary storing cached values.
        max_size: Maximum cache size.
        hits: Number of cache hits.
        misses: Number of cache misses.
        lock: Thread lock for synchronization.
    """

    def __init__(self, max_size: int = 1000) -> None:
        """Initialize LRU cache.

        Args:
            max_size: Maximum cache size.
        """
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
        self.lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None.
        """
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                self.hits += 1
                return self.cache[key]

            self.misses += 1
            return None

    def put(self, key: str, value: Any) -> None:
        """Put value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
        """
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                self.cache[key] = value
                return

            self.cache[key] = value

            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)

    def clear(self) -> None:
        """Clear cache."""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Cache stats.
        """
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0.0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "size": len(self.cache),
            "max_size": self.max_size,
        }
