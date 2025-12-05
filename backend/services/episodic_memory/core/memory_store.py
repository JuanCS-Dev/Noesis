"""
Episodic Memory: Memory Store
=============================

Core logic for storing and retrieving memories.
Implements MIRIX-compatible memory operations including:
- consolidate_to_vault: Move high-importance memories to long-term storage
- decay_importance: Apply Ebbinghaus forgetting curve
- Vector search integration (via Qdrant)

Based on: MIRIX (arXiv:2507.07957) + Mem0 (arXiv:2504.19413)
"""

from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

from models.memory import Memory, MemoryQuery, MemorySearchResult, MemoryType


logger = logging.getLogger(__name__)


class MemoryStore:
    """
    Storage engine for episodic memories with MIRIX enhancements.

    Manages persistence and retrieval of memory objects.
    Supports consolidation, decay, and multi-type context retrieval.
    """

    def __init__(self) -> None:
        """Initialize the memory store."""
        self._storage: Dict[str, Memory] = {}
        logger.info("MemoryStore initialized (in-memory)")

    async def store(
        self,
        content: str,
        memory_type: MemoryType,
        context: Optional[Dict[str, Any]] = None
    ) -> Memory:
        """
        Store a new memory.

        Args:
            content: The memory content
            memory_type: Type of memory
            context: Optional metadata

        Returns:
            The created Memory object
        """
        memory_id = str(uuid.uuid4())
        memory = Memory(
            memory_id=memory_id,
            type=memory_type,
            content=content,
            context=context or {},
            timestamp=datetime.now()
        )

        self._storage[memory_id] = memory
        logger.info("Stored memory: %s (type=%s)", memory_id, memory_type)
        return memory

    async def retrieve(self, query: MemoryQuery) -> MemorySearchResult:
        """
        Retrieve memories based on a query.

        Args:
            query: Search criteria

        Returns:
            Search results
        """
        results: List[Memory] = []

        # Simple keyword search for now
        query_terms = query.query_text.lower().split()

        for memory in self._storage.values():
            # Filter by type if specified
            if query.type and memory.type != query.type:
                continue

            # Filter by importance
            if memory.importance < query.min_importance:
                continue

            # Check content match
            content_lower = memory.content.lower()
            if any(term in content_lower for term in query_terms):
                results.append(memory)

        # Sort by timestamp (newest first) as a simple heuristic
        results.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply limit
        limited_results = results[:query.limit]

        return MemorySearchResult(
            memories=limited_results,
            total_found=len(results)
        )

    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """
        Get a specific memory by ID.

        Args:
            memory_id: ID to look up

        Returns:
            Memory object or None
        """
        return self._storage.get(memory_id)

    async def delete(self, memory_id: str) -> bool:
        """
        Delete a memory.

        Args:
            memory_id: ID to delete

        Returns:
            True if deleted, False if not found
        """
        if memory_id in self._storage:
            del self._storage[memory_id]
            logger.info("Deleted memory: %s", memory_id)
            return True
        return False

    async def consolidate_to_vault(
        self,
        threshold: float = 0.8,
        min_age_days: int = 7,
        min_access_count: int = 2
    ) -> Dict[str, int]:
        """
        Move high-importance memories to vault (long-term storage).

        Based on: Mem0 consolidation strategy + MIRIX vault concept.

        Criteria for consolidation:
        1. importance >= threshold
        2. age >= min_age_days
        3. access_count >= min_access_count
        4. Not already VAULT or CORE type

        Args:
            threshold: Minimum importance score (0.0-1.0)
            min_age_days: Only consolidate memories older than this
            min_access_count: Minimum retrieval count

        Returns:
            Count of consolidated memories by original type

        Example:
            >>> counts = await store.consolidate_to_vault(0.85)
            >>> counts
            {"episodic": 12, "semantic": 5, "procedural": 3}
        """
        consolidated: Dict[str, int] = defaultdict(int)
        cutoff_date = datetime.utcnow() - timedelta(days=min_age_days)

        for memory in list(self._storage.values()):
            # Skip vault and core (already permanent)
            if memory.type in [MemoryType.VAULT, MemoryType.CORE]:
                continue

            # Check consolidation criteria
            if (memory.importance >= threshold and
                memory.timestamp < cutoff_date and
                memory.access_count >= min_access_count):

                original_type = memory.type.value
                memory.type = MemoryType.VAULT
                memory.context["original_type"] = original_type
                memory.context["consolidated_at"] = datetime.utcnow().isoformat()

                consolidated[original_type] += 1

        total = sum(consolidated.values())
        logger.info("Consolidated %d memories to vault: %s", total, dict(consolidated))
        return dict(consolidated)

    async def decay_importance(
        self,
        decay_factor: float = 0.995,
        boost_recent_access: bool = True,
        delete_threshold: float = 0.05
    ) -> Dict[str, int]:
        """
        Apply Ebbinghaus forgetting curve to importance scores.

        Based on: Stanford Generative Agents (2023) + Ebbinghaus research.

        Formula: new_importance = old_importance * (decay_factor ^ hours_elapsed)

        Default decay_factor=0.995 means:
        - After 24h: 88.6% of original
        - After 7d: 42.8% of original
        - After 30d: 2.7% of original

        Args:
            decay_factor: Hourly decay rate (default: 0.995)
            boost_recent_access: Boost memories accessed in last 24h
            delete_threshold: Delete memories below this importance

        Returns:
            Statistics: {"decayed": N, "boosted": N, "deleted": N}

        Example:
            >>> stats = await store.decay_importance()
            >>> stats
            {"decayed": 150, "boosted": 12, "deleted": 5}
        """
        stats = {"decayed": 0, "boosted": 0, "deleted": 0}
        now = datetime.utcnow()
        to_delete: List[str] = []

        for memory_id, memory in self._storage.items():
            # Skip vault and core (don't decay)
            if memory.type in [MemoryType.VAULT, MemoryType.CORE]:
                continue

            # Calculate hours since creation
            hours_elapsed = (now - memory.timestamp).total_seconds() / 3600

            # Apply decay
            decayed = memory.importance * (decay_factor ** hours_elapsed)

            # Boost if accessed recently
            if boost_recent_access and memory.last_accessed:
                hours_since_access = (now - memory.last_accessed).total_seconds() / 3600
                if hours_since_access < 24:
                    # Boost proportional to recency (max 0.1)
                    boost = 0.1 * (1 - hours_since_access / 24)
                    decayed = min(1.0, decayed + boost)
                    stats["boosted"] += 1

            memory.importance = decayed
            stats["decayed"] += 1

            # Mark for deletion if below threshold
            if decayed < delete_threshold:
                to_delete.append(memory_id)

        # Delete low-importance memories
        for memory_id in to_delete:
            del self._storage[memory_id]
            stats["deleted"] += 1

        logger.info("Decay complete: %s", stats)
        return stats

    async def get_memories_by_type(
        self,
        memory_type: MemoryType,
        limit: int = 10
    ) -> List[Memory]:
        """
        Get memories filtered by type, sorted by importance.

        Args:
            memory_type: Type to filter by
            limit: Maximum number of results

        Returns:
            List of memories sorted by importance (descending)
        """
        memories = [m for m in self._storage.values() if m.type == memory_type]
        memories.sort(key=lambda m: m.importance, reverse=True)
        return memories[:limit]

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get memory store statistics.

        Returns:
            Statistics including counts by type, average importance, etc.
        """
        type_counts: Dict[str, int] = defaultdict(int)
        total_importance = 0.0

        for memory in self._storage.values():
            type_counts[memory.type.value] += 1
            total_importance += memory.importance

        total = len(self._storage)
        return {
            "total_memories": total,
            "by_type": dict(type_counts),
            "avg_importance": total_importance / total if total > 0 else 0.0
        }
