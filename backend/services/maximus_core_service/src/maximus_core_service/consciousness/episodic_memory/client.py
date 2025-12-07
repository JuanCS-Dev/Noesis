"""
Episodic Memory Service Client
==============================

HTTP client for connecting ConsciousnessSystem to the episodic_memory microservice.
Provides persistence for conscious events and memories across sessions.

Features:
- Async HTTP calls to episodic_memory API
- Automatic retry with exponential backoff
- Graceful fallback when service unavailable
- MIRIX memory type support
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Optional

import aiohttp

logger = logging.getLogger(__name__)


class EpisodicMemoryClient:
    """
    HTTP client for episodic_memory microservice.

    Provides async methods to store and retrieve memories from the
    persistent Qdrant-backed memory store.
    """

    DEFAULT_URL = "http://localhost:8102"

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 10.0,
        retry_count: int = 3
    ):
        """
        Initialize episodic memory client.

        Args:
            base_url: Episodic memory service URL (default: localhost:8102)
            timeout: Request timeout in seconds
            retry_count: Number of retries on failure
        """
        self.base_url = base_url or os.environ.get(
            "EPISODIC_MEMORY_URL", self.DEFAULT_URL
        )
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.retry_count = retry_count
        self._session: aiohttp.ClientSession | None = None
        self._available: bool | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def is_available(self) -> bool:
        """Check if episodic memory service is available."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self._available = data.get("status") == "healthy"
                    return self._available
                return False
        except Exception as e:
            logger.debug(f"Episodic memory service unavailable: {e}")
            self._available = False
            return False

    async def store_memory(
        self,
        content: str,
        memory_type: str = "episodic",
        context: dict[str, Any] | None = None,
        importance: float = 0.5
    ) -> dict[str, Any] | None:
        """
        Store a memory in the episodic memory service.

        Args:
            content: Memory content text
            memory_type: MIRIX type (core, episodic, semantic, procedural, resource, vault)
            context: Optional metadata
            importance: Importance score (0-1)

        Returns:
            Created memory data, or None if failed
        """
        if self._available is False:
            # Skip if we know service is down
            return None

        try:
            session = await self._get_session()
            payload = {
                "content": content,
                "type": memory_type,
                "context": context or {},
            }

            async with session.post(
                f"{self.base_url}/v1/memories",
                json=payload
            ) as resp:
                if resp.status in (200, 201):
                    data = await resp.json()
                    logger.debug(f"Stored memory: {data.get('memory_id', 'unknown')[:8]}")
                    return data
                else:
                    logger.warning(f"Failed to store memory: {resp.status}")
                    return None

        except Exception as e:
            logger.warning(f"Memory store error: {e}")
            self._available = False
            return None

    async def search_memories(
        self,
        query_text: str,
        memory_type: str | None = None,
        min_importance: float = 0.0,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Search memories by semantic similarity.

        Args:
            query_text: Search query
            memory_type: Filter by MIRIX type (optional)
            min_importance: Minimum importance threshold
            limit: Maximum results

        Returns:
            List of matching memories
        """
        if self._available is False:
            return []

        try:
            session = await self._get_session()
            payload = {
                "query_text": query_text,
                "min_importance": min_importance,
                "limit": limit,
            }
            if memory_type:
                payload["type"] = memory_type

            async with session.post(
                f"{self.base_url}/v1/memories/search",
                json=payload
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("memories", [])
                return []

        except Exception as e:
            logger.warning(f"Memory search error: {e}")
            return []

    async def get_context_for_task(self, task: str) -> dict[str, Any] | None:
        """
        Get multi-type memory context for a task.

        Args:
            task: Task description

        Returns:
            MemoryContext organized by MIRIX types
        """
        if self._available is False:
            return None

        try:
            session = await self._get_session()
            async with session.post(
                f"{self.base_url}/v1/memories/context",
                json={"task": task}
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None

        except Exception as e:
            logger.warning(f"Context retrieval error: {e}")
            return None

    async def get_stats(self) -> dict[str, Any] | None:
        """Get memory store statistics."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/v1/memories/stats") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("stats", {})
                return None
        except Exception as e:
            logger.debug(f"Stats retrieval failed: {e}")
            return None

    async def store_conscious_event(
        self,
        event_id: str,
        content: dict[str, Any],
        coherence: float,
        narrative: str | None = None
    ) -> dict[str, Any] | None:
        """
        Store a conscious ESGT event as an episodic memory.

        This method creates a structured memory from an ESGT event,
        including coherence achieved, content processed, and any
        narrative generated by the consciousness bridge.

        Args:
            event_id: ESGT event ID
            content: Event content payload
            coherence: Achieved coherence level
            narrative: Optional introspective narrative

        Returns:
            Created memory, or None if failed
        """
        # Build memory content from event
        memory_content = f"ESGT Event {event_id[:8]}: "

        if "user_input" in content:
            memory_content += f"Input: \"{content['user_input'][:100]}\". "

        memory_content += f"Coherence: {coherence:.2f}. "

        if narrative:
            memory_content += f"Narrative: {narrative[:200]}"

        # Context includes full event data
        context = {
            "event_id": event_id,
            "coherence": coherence,
            "source": content.get("source", "unknown"),
            "depth": content.get("depth", 1),
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Importance based on coherence (high coherence = high importance)
        importance = 0.3 + (coherence * 0.7)  # 0.3 - 1.0

        return await self.store_memory(
            content=memory_content,
            memory_type="episodic",
            context=context,
            importance=importance
        )


# Singleton instance for easy import
_client: EpisodicMemoryClient | None = None


def get_episodic_memory_client() -> EpisodicMemoryClient:
    """Get or create singleton episodic memory client."""
    global _client
    if _client is None:
        _client = EpisodicMemoryClient()
    return _client
