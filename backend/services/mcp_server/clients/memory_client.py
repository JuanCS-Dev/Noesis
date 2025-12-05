"""
Episodic Memory Service Client
==============================

Client for episodic_memory service.

Follows CODE_CONSTITUTION: Clarity Over Cleverness.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, cast

from clients.base_client import BaseHTTPClient
from config import MCPServerConfig


class MemoryClient:
    """Client for Episodic Memory service.

    Provides methods to store, search, and consolidate memories.

    Example:
        >>> client = MemoryClient(config)
        >>> memory_id = await client.store("User said hello", "experience")
        >>> results = await client.search("greeting", limit=5)
    """

    def __init__(self, config: MCPServerConfig):
        """Initialize Memory client.

        Args:
            config: Service configuration
        """
        self.config = config
        self.client = BaseHTTPClient(config, config.memory_url)

    async def store(
        self,
        content: str,
        memory_type: str,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Store memory in episodic system.

        Args:
            content: Memory content
            memory_type: Type (experience, fact, procedure, etc.)
            importance: Importance score 0.0-1.0
            tags: Optional tags for search

        Returns:
            Memory ID and metadata

        Example:
            >>> result = await client.store(
            ...     "Task completed successfully",
            ...     "experience",
            ...     importance=0.8,
            ...     tags=["success", "completion"]
            ... )
        """
        payload = {
            "content": content,
            "memory_type": memory_type,
            "importance": importance,
            "tags": tags or [],
        }
        result = await self.client.post("/v1/memories", json=payload)
        return result

    async def search(
        self,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search memories using semantic search.

        Args:
            query: Search query
            memory_type: Filter by type (optional)
            limit: Max results (1-100)

        Returns:
            List of memories ranked by relevance

        Example:
            >>> results = await client.search("authentication", limit=10)
            >>> for memory in results:
            ...     print(memory["content"])
        """
        params: Dict[str, Any] = {"query": query, "limit": limit}
        if memory_type:
            params["memory_type"] = memory_type

        result = await self.client.get("/v1/memories/search", params=params)
        # API returns {"memories": [...]}
        memories = result.get("memories", [])
        return cast(List[Dict[str, Any]], memories)

    async def get_context_for_task(self, task: str) -> Dict[str, Any]:
        """Get relevant context for a task.

        Combines all 6 memory types to provide comprehensive context.

        Args:
            task: Task description

        Returns:
            Context dict with memories from all types

        Example:
            >>> context = await client.get_context_for_task("write tests")
            >>> context["procedural"]  # Skills related to testing
        """
        payload = {"task": task}
        result = await self.client.post("/v1/memories/context", json=payload)
        return result

    async def consolidate_to_vault(
        self, threshold: float = 0.8
    ) -> Dict[str, int]:
        """Consolidate high-importance memories to vault.

        Args:
            threshold: Importance threshold (0.0-1.0)

        Returns:
            Counts by memory type consolidated

        Example:
            >>> counts = await client.consolidate_to_vault(0.8)
            >>> counts["experience"]  # Number consolidated
            15
        """
        payload = {"threshold": threshold}
        result = await self.client.post("/v1/memories/consolidate", json=payload)
        return result

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics.

        Returns:
            Stats by memory type
        """
        result = await self.client.get("/v1/memories/stats")
        return result

    async def close(self) -> None:
        """Close client connections."""
        await self.client.close()
