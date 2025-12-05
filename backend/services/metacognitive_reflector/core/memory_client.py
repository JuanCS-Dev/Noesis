"""
MAXIMUS 2.0 - Memory Client
============================

Real integration with Episodic Memory service (MIRIX).
Supports HTTP API calls with in-memory fallback.

Based on:
- MIRIX Memory Architecture
- Qdrant vector search patterns
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models.reflection import MemoryUpdate
from .memory_models import MemoryEntry, MemoryType, SearchResult


class MemoryClient:
    """
    Client for Episodic Memory service integration.

    Supports:
    - HTTP API calls to memory service
    - In-memory fallback for development/testing
    - Semantic search via embeddings
    - Memory updates and retrieval

    Usage:
        client = MemoryClient()
        await client.store("Agent learned X", MemoryType.SEMANTIC)
        results = await client.search("What did agent learn?")
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_seconds: float = 5.0,
        use_fallback: bool = True,
    ) -> None:
        """
        Initialize memory client.

        Args:
            base_url: Memory service URL (None for fallback only)
            timeout_seconds: HTTP timeout
            use_fallback: Use in-memory when service unavailable
        """
        self._base_url = base_url
        self._timeout = timeout_seconds
        self._use_fallback = use_fallback
        self._http_client: Optional[Any] = None

        # In-memory fallback storage
        self._fallback_storage: Dict[str, MemoryEntry] = {}
        self._memory_counter = 0

    async def _get_http_client(self) -> Any:
        """Lazy initialize HTTP client."""
        if self._http_client is None and self._base_url:
            try:
                # pylint: disable=import-outside-toplevel
                import httpx
                self._http_client = httpx.AsyncClient(
                    base_url=self._base_url,
                    timeout=self._timeout,
                )
            except ImportError:
                pass  # httpx not available, will use in-memory storage
        return self._http_client

    async def store(
        self,
        content: str,
        memory_type: MemoryType,
        importance: float = 0.5,
        context: Optional[Dict[str, Any]] = None,
    ) -> MemoryEntry:
        """
        Store a new memory.

        Args:
            content: Memory content
            memory_type: Type of memory
            importance: Importance score (0-1)
            context: Additional metadata

        Returns:
            Created MemoryEntry
        """
        # Try HTTP first
        if self._base_url:
            try:
                return await self._store_http(
                    content, memory_type, importance, context
                )
            except (ConnectionError, TimeoutError, OSError):
                if not self._use_fallback:
                    raise

        # Fallback to in-memory
        return await self._store_fallback(content, memory_type, importance, context)

    async def _store_http(
        self,
        content: str,
        memory_type: MemoryType,
        importance: float,
        context: Optional[Dict[str, Any]],
    ) -> MemoryEntry:
        """Store via HTTP API."""
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

    async def _store_fallback(
        self,
        content: str,
        memory_type: MemoryType,
        importance: float,
        context: Optional[Dict[str, Any]],
    ) -> MemoryEntry:
        """Store in fallback memory."""
        self._memory_counter += 1
        memory_id = f"mem_{self._memory_counter}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        entry = MemoryEntry(
            memory_id=memory_id,
            content=content,
            memory_type=memory_type,
            importance=importance,
            context=context or {},
            timestamp=datetime.now(),
        )

        self._fallback_storage[memory_id] = entry
        return entry

    async def search(
        self,
        query: str,
        memory_types: Optional[List[MemoryType]] = None,
        limit: int = 10,
        min_importance: float = 0.0,
    ) -> SearchResult:
        """
        Search memories.

        Args:
            query: Search query
            memory_types: Filter by types
            limit: Max results
            min_importance: Minimum importance threshold

        Returns:
            SearchResult with matching memories
        """
        start_time = datetime.now()

        # Try HTTP first
        if self._base_url:
            try:
                return await self._search_http(
                    query, memory_types, limit, min_importance
                )
            except (ConnectionError, TimeoutError, OSError):
                if not self._use_fallback:
                    raise

        # Fallback to in-memory
        result = await self._search_fallback(
            query, memory_types, limit, min_importance
        )

        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        result.query_time_ms = elapsed
        return result

    async def _search_http(
        self,
        query: str,
        memory_types: Optional[List[MemoryType]],
        limit: int,
        min_importance: float,
    ) -> SearchResult:
        """Search via HTTP API."""
        client = await self._get_http_client()
        if not client:
            raise ConnectionError("HTTP client not available")

        params = {
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

    async def _search_fallback(
        self,
        query: str,
        memory_types: Optional[List[MemoryType]],
        limit: int,
        min_importance: float,
    ) -> SearchResult:
        """Search in fallback memory."""
        query_lower = query.lower()
        query_terms = query_lower.split()

        results = []
        for entry in self._fallback_storage.values():
            # Filter by type
            if memory_types and entry.memory_type not in memory_types:
                continue

            # Filter by importance
            if entry.importance < min_importance:
                continue

            # Simple keyword match
            content_lower = entry.content.lower()
            if any(term in content_lower for term in query_terms):
                results.append(entry)

        # Sort by importance and timestamp
        results.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)

        return SearchResult(
            memories=results[:limit],
            total_found=len(results),
        )

    async def get(self, memory_id: str) -> Optional[MemoryEntry]:
        """
        Get a specific memory by ID.

        Args:
            memory_id: Memory identifier

        Returns:
            MemoryEntry or None if not found
        """
        # Try HTTP first
        if self._base_url:
            try:
                return await self._get_http(memory_id)
            except (ConnectionError, TimeoutError, OSError):
                if not self._use_fallback:
                    raise

        # Fallback
        return self._fallback_storage.get(memory_id)

    async def _get_http(self, memory_id: str) -> Optional[MemoryEntry]:
        """Get via HTTP API."""
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

    async def delete(self, memory_id: str) -> bool:
        """
        Delete a memory.

        Args:
            memory_id: Memory to delete

        Returns:
            True if deleted
        """
        # Try HTTP first
        if self._base_url:
            try:
                return await self._delete_http(memory_id)
            except (ConnectionError, TimeoutError, OSError):
                if not self._use_fallback:
                    raise

        # Fallback
        if memory_id in self._fallback_storage:
            del self._fallback_storage[memory_id]
            return True
        return False

    async def _delete_http(self, memory_id: str) -> bool:
        """Delete via HTTP API."""
        client = await self._get_http_client()
        if not client:
            raise ConnectionError("HTTP client not available")

        response = await client.delete(f"/memories/{memory_id}")
        return response.status_code == 200

    async def apply_updates(
        self,
        updates: List[MemoryUpdate],
    ) -> Dict[str, Any]:
        """
        Apply memory updates from reflection.

        Args:
            updates: List of updates to apply

        Returns:
            Status dictionary
        """
        results = []
        for update in updates:
            # Map update type to memory type
            memory_type = self._map_update_type(update.update_type.value)

            entry = await self.store(
                content=update.content,
                memory_type=memory_type,
                importance=update.confidence,  # MemoryUpdate uses 'confidence'
                context={"source": "reflection", "original_type": update.update_type.value},
            )
            results.append({
                "memory_id": entry.memory_id,
                "status": "stored",
            })

        return {
            "status": "success",
            "updates_applied": len(results),
            "results": results,
        }

    def _map_update_type(self, update_type: str) -> MemoryType:
        """Map MemoryUpdateType to MemoryType."""
        mapping = {
            "NEW_KNOWLEDGE": MemoryType.SEMANTIC,
            "CORRECTION": MemoryType.SEMANTIC,
            "PATTERN": MemoryType.PROCEDURAL,
            "REFLECTION": MemoryType.REFLECTION,
        }
        return mapping.get(update_type, MemoryType.EPISODIC)

    async def store_reflection(
        self,
        agent_id: str,
        reflection_type: str,
        content: str,
        verdict_data: Optional[Dict[str, Any]] = None,
    ) -> MemoryEntry:
        """
        Store a reflection memory.

        Args:
            agent_id: Agent that generated reflection
            reflection_type: Type of reflection
            content: Reflection content
            verdict_data: Associated verdict data

        Returns:
            Created memory entry
        """
        return await self.store(
            content=content,
            memory_type=MemoryType.REFLECTION,
            importance=0.7,
            context={
                "agent_id": agent_id,
                "reflection_type": reflection_type,
                "verdict_data": verdict_data or {},
            },
        )

    async def get_agent_history(
        self,
        agent_id: str,
        limit: int = 20,
    ) -> List[MemoryEntry]:
        """
        Get memory history for an agent.

        Args:
            agent_id: Agent identifier
            limit: Max entries

        Returns:
            List of memory entries
        """
        result = await self.search(
            query=agent_id,
            limit=limit,
        )
        return [m for m in result.memories if m.context.get("agent_id") == agent_id]

    async def health_check(self) -> Dict[str, Any]:
        """Check memory client health."""
        http_healthy = False

        if self._base_url:
            try:
                client = await self._get_http_client()
                if client:
                    response = await asyncio.wait_for(
                        client.get("/health"),
                        timeout=2.0,
                    )
                    http_healthy = response.status_code == 200
            except (ConnectionError, TimeoutError, OSError, asyncio.TimeoutError):
                pass  # HTTP check failed, fallback will be used

        return {
            "healthy": http_healthy or self._use_fallback,
            "http_available": http_healthy,
            "fallback_enabled": self._use_fallback,
            "fallback_entries": len(self._fallback_storage),
            "base_url": self._base_url,
        }

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
