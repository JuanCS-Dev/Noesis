"""
Memory Hierarchy - 6-Layer MIRIX Architecture
==============================================

Manages 6 types of memory with caching and type-specific optimization.

Performance:
- L1 Cache: In-memory (0ms) - CORE + VAULT
- L2 Hot Cache: <10ms - Recent EPISODIC + SEMANTIC
- L3 Qdrant: <10ms - All types
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
from datetime import datetime

from core.qdrant_client import QdrantClient
from models.memory_types import (
    TypedMemory,
    MemoryType,
    MemoryPriority,
    MemoryTypeConfig
)
from utils.logging_config import get_logger

logger = get_logger(__name__)


class MemoryHierarchy:
    """
    6-layer memory hierarchy with caching and type-specific optimization.

    Cache Layers (L1 → L3):
    - L1: In-memory dict (CRITICAL priority only)
    - L2: Hot cache (HIGH/MEDIUM, accessed in last 24h)
    - L3: Qdrant (all memories)

    Features:
    - Type-specific TTL enforcement
    - Priority-based caching
    - Automatic cache eviction
    - Access tracking for optimization

    Example:
        >>> hierarchy = MemoryHierarchy(qdrant_client)
        >>> await hierarchy.store(
        ...     memory=TypedMemory(type=MemoryType.CORE, ...)
        ... )
        >>> results = await hierarchy.search(
        ...     query_embedding=[...],
        ...     memory_types=[MemoryType.CORE, MemoryType.SEMANTIC]
        ... )
    """

    def __init__(
        self,
        qdrant_client: QdrantClient,
        l1_max_size: int = 100,   # CRITICAL memories only
        l2_max_size: int = 1000   # HOT memories
    ):
        """
        Initialize memory hierarchy.

        Args:
            qdrant_client: Qdrant client for L3 storage
            l1_max_size: Max L1 cache size (CRITICAL only)
            l2_max_size: Max L2 cache size (HOT)
        """
        self.qdrant = qdrant_client

        # L1 Cache: CRITICAL memories (CORE + VAULT)
        self.l1_cache: Dict[str, TypedMemory] = {}
        self.l1_max_size = l1_max_size

        # L2 Cache: HOT memories (recently accessed)
        self.l2_cache: Dict[str, TypedMemory] = {}
        self.l2_max_size = l2_max_size

        # Statistics
        self.stats = {
            "l1_hits": 0,
            "l2_hits": 0,
            "l3_hits": 0,
            "total_stores": 0,
            "total_searches": 0
        }

        logger.info(
            "memory_hierarchy_initialized",
            extra={
                "l1_max": l1_max_size,
                "l2_max": l2_max_size
            }
        )

    async def store(self, memory: TypedMemory) -> None:
        """
        Store memory in hierarchy with type-specific handling.

        Args:
            memory: Typed memory to store
        """
        # Get type configuration
        config = MemoryTypeConfig.for_type(memory.type)

        # Set TTL if not specified
        if memory.ttl_days is None:
            memory.ttl_days = config.ttl_days

        # Encrypt if required (Vault)
        if config.encryption_required and not memory.encrypted:
            # Future: Implement encryption
            logger.warning(
                "encryption_required_but_not_implemented",
                extra={"memory_id": memory.id}
            )

        # Store in L3 (Qdrant)
        await self.qdrant.store_memory(
            memory_id=memory.id,
            embedding=memory.embedding,
            metadata={
                "type": memory.type.value,
                "content": memory.content,
                "metadata": memory.metadata,
                "timestamp": memory.timestamp.isoformat(),
                "ttl_days": memory.ttl_days,
                "access_count": memory.access_count,
                "encrypted": memory.encrypted
            }
        )

        # Cache based on priority
        if config.priority == MemoryPriority.CRITICAL:
            self._add_to_l1(memory)
        elif config.priority >= MemoryPriority.HIGH:
            self._add_to_l2(memory)

        self.stats["total_stores"] += 1

        logger.debug(
            "memory_stored",
            extra={
                "memory_id": memory.id,
                "type": memory.type.value,
                "priority": config.priority.name
            }
        )

    async def search(
        self,
        query_embedding: List[float],
        memory_types: Optional[List[MemoryType]] = None,
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[TypedMemory]:
        """
        Search memories with cache optimization.

        Args:
            query_embedding: Query vector
            memory_types: Filter by memory types
            limit: Maximum results
            score_threshold: Minimum similarity score

        Returns:
            List of matching typed memories
        """
        self.stats["total_searches"] += 1

        # 1. Check L1 cache (CRITICAL only)
        has_critical = MemoryType.CORE in memory_types if memory_types else True
        has_vault = MemoryType.VAULT in memory_types if memory_types else True
        if memory_types is None or has_critical or has_vault:
            l1_results = self._search_l1(query_embedding, limit)
            if l1_results:
                self.stats["l1_hits"] += 1
                logger.debug("l1_cache_hit", extra={"count": len(l1_results)})
                return l1_results[:limit]

        # 2. Check L2 cache (HOT)
        l2_results = self._search_l2(query_embedding, memory_types, limit)
        if len(l2_results) >= limit:
            self.stats["l2_hits"] += 1
            logger.debug("l2_cache_hit", extra={"count": len(l2_results)})
            return l2_results[:limit]

        # 3. Search L3 (Qdrant)
        filter_conditions: Dict[str, Any] = {}
        if memory_types:
            # Qdrant doesn't support list filtering directly, search all then filter
            pass

        l3_results = await self.qdrant.search_memory(
            query_embedding=query_embedding,
            limit=limit * 2,  # Fetch extra for filtering
            score_threshold=score_threshold,
            filter_conditions=filter_conditions
        )

        # Convert to TypedMemory and filter by type
        memories = []
        for result in l3_results:
            metadata = result["metadata"]

            # Filter by type if specified
            if memory_types and metadata.get("type") not in [t.value for t in memory_types]:
                continue

            memory = TypedMemory(
                id=result["id"],
                type=MemoryType(metadata["type"]),
                content=metadata["content"],
                embedding=query_embedding,  # Approximate (not stored in Qdrant)
                metadata=metadata.get("metadata", {}),
                timestamp=datetime.fromisoformat(metadata["timestamp"]),
                ttl_days=metadata.get("ttl_days"),
                access_count=metadata.get("access_count", 0),
                encrypted=metadata.get("encrypted", False)
            )

            # Record access
            memory.record_access()

            # Update cache
            if memory.should_cache():
                config = MemoryTypeConfig.for_type(memory.type)
                if config.priority == MemoryPriority.CRITICAL:
                    self._add_to_l1(memory)
                elif config.priority >= MemoryPriority.HIGH:
                    self._add_to_l2(memory)

            memories.append(memory)

            if len(memories) >= limit:
                break

        self.stats["l3_hits"] += 1
        logger.debug(
            "l3_qdrant_search",
            extra={"count": len(memories)}
        )

        return memories

    async def get_by_id(self, memory_id: str) -> Optional[TypedMemory]:
        """
        Get memory by ID with cache lookup.

        Args:
            memory_id: Memory identifier

        Returns:
            Typed memory or None
        """
        # Check L1
        if memory_id in self.l1_cache:
            self.stats["l1_hits"] += 1
            return self.l1_cache[memory_id]

        # Check L2
        if memory_id in self.l2_cache:
            self.stats["l2_hits"] += 1
            return self.l2_cache[memory_id]

        # L3: Not implemented (Qdrant get_by_id)
        # Future: Add get_by_id to QdrantClient
        return None

    async def delete(self, memory_id: str) -> None:
        """
        Delete memory from all layers.

        Args:
            memory_id: Memory identifier
        """
        # Remove from caches
        self.l1_cache.pop(memory_id, None)
        self.l2_cache.pop(memory_id, None)

        # Remove from L3
        await self.qdrant.delete_memory(memory_id)

        logger.debug("memory_deleted", extra={"memory_id": memory_id})

    async def cleanup_expired(self) -> int:
        """
        Remove expired memories based on TTL.

        Returns:
            Number of memories cleaned up
        """
        cleaned = 0

        # Check L1 cache
        expired_l1 = [mid for mid, mem in self.l1_cache.items() if mem.is_expired()]
        for mid in expired_l1:
            await self.delete(mid)
            cleaned += 1

        # Check L2 cache
        expired_l2 = [mid for mid, mem in self.l2_cache.items() if mem.is_expired()]
        for mid in expired_l2:
            await self.delete(mid)
            cleaned += 1

        if cleaned > 0:
            logger.info("expired_memories_cleaned", extra={"count": cleaned})

        return cleaned

    def _add_to_l1(self, memory: TypedMemory) -> None:
        """Add memory to L1 cache (CRITICAL only)."""
        if len(self.l1_cache) >= self.l1_max_size:
            # Evict least recently accessed
            lru_id = min(
                self.l1_cache.items(),
                key=lambda x: x[1].last_accessed or datetime.min
            )[0]
            self.l1_cache.pop(lru_id)

        self.l1_cache[memory.id] = memory

    def _add_to_l2(self, memory: TypedMemory) -> None:
        """Add memory to L2 cache (HOT)."""
        if len(self.l2_cache) >= self.l2_max_size:
            # Evict least recently accessed
            lru_id = min(
                self.l2_cache.items(),
                key=lambda x: x[1].last_accessed or datetime.min
            )[0]
            self.l2_cache.pop(lru_id)

        self.l2_cache[memory.id] = memory

    def _search_l1(
        self, _query_embedding: List[float], limit: int
    ) -> List[TypedMemory]:
        """Simple L1 cache search (returns all CRITICAL memories)."""
        return list(self.l1_cache.values())[:limit]

    def _search_l2(
        self,
        _query_embedding: List[float],
        memory_types: Optional[List[MemoryType]],
        limit: int
    ) -> List[TypedMemory]:
        """Simple L2 cache search (filter by type)."""
        results = []
        for memory in self.l2_cache.values():
            if memory_types is None or memory.type in memory_types:
                results.append(memory)
            if len(results) >= limit:
                break
        return results

    def get_stats(self) -> Dict[str, Any]:
        """
        Get hierarchy statistics.

        Returns:
            Dictionary of statistics
        """
        total_requests = self.stats["l1_hits"] + self.stats["l2_hits"] + self.stats["l3_hits"]

        return {
            **self.stats,
            "l1_size": len(self.l1_cache),
            "l2_size": len(self.l2_cache),
            "cache_hit_rate": (
                (self.stats["l1_hits"] + self.stats["l2_hits"]) / max(1, total_requests)
            ) * 100
        }
