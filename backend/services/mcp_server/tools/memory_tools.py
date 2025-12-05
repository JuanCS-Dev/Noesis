"""
Episodic Memory MCP Tools
=========================

MCP tools for episodic_memory service (MIRIX 6-type system).

Follows CODE_CONSTITUTION: Clarity Over Cleverness.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MemoryStoreRequest(BaseModel):
    """Request model for memory storage."""

    content: str = Field(..., min_length=1, max_length=50000)
    memory_type: str = Field(
        ...,
        pattern="^(experience|fact|procedure|reflection|core|resource|vault)$"
    )
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    tags: List[str] = Field(default_factory=list, max_length=10)


async def memory_store(
    content: str,
    memory_type: str,
    importance: float = 0.5,
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Armazena memória no sistema episódico.

    Supports MIRIX 6-type memory system:
    - experience: Temporal experiences (decay over time)
    - fact: Factual knowledge (confidence-based)
    - procedure: Skills/methods (success-rate tracking)
    - reflection: Self-analysis (meta-cognitive insights)
    - core: Identity/values (permanent, no decay)
    - resource: Tool/API cache (TTL-based)
    - vault: Consolidated long-term (high-confidence only)

    Args:
        content: Memory content (max 50k chars)
        memory_type: MIRIX type (7 options)
        importance: Score 0.0-1.0 for consolidation priority
        tags: Optional labels for search (max 10)

    Returns:
        Memory ID and metadata

    Example:
        >>> memory = await memory_store(
        ...     "Successfully generated 'double' tool with 100% success rate",
        ...     "experience",
        ...     importance=0.9,
        ...     tags=["success", "tool_generation"]
        ... )
        >>> memory["id"]
        "mem_12345"
    """
    request = MemoryStoreRequest(
        content=content,
        memory_type=memory_type,
        importance=importance,
        tags=tags or []
    )

    from clients.memory_client import MemoryClient
    from config import get_config

    config = get_config()
    client = MemoryClient(config)

    try:
        result = await client.store(
            request.content,
            request.memory_type,
            request.importance,
            request.tags
        )
        return result
    finally:
        await client.close()


async def memory_search(
    query: str,
    memory_type: Optional[str] = None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Busca memórias relevantes usando semantic search.

    Uses cached embeddings for fast retrieval.
    Results ranked by relevance + recency + importance.

    Args:
        query: Search query
        memory_type: Filter by MIRIX type (optional)
        limit: Max results (1-100, default: 5)

    Returns:
        List of memories ranked by relevance

    Example:
        >>> results = await memory_search("tool generation", limit=3)
        >>> results[0]["content"]
        "Successfully generated..."
    """
    from clients.memory_client import MemoryClient
    from config import get_config

    config = get_config()
    client = MemoryClient(config)

    try:
        result = await client.search(query, memory_type, limit)
        return result
    finally:
        await client.close()


async def memory_consolidate(threshold: float = 0.8) -> Dict[str, int]:
    """
    Consolida memórias high-importance para vault.

    Batch operation that moves memories with importance >= threshold
    to permanent vault. Runs async in background.

    Args:
        threshold: Importance threshold (0.0-1.0, default: 0.8)

    Returns:
        Counts by memory type consolidated

    Example:
        >>> counts = await memory_consolidate(0.85)
        >>> counts["experience"]
        12
    """
    from clients.memory_client import MemoryClient
    from config import get_config

    config = get_config()
    client = MemoryClient(config)

    try:
        result = await client.consolidate_to_vault(threshold)
        return result
    finally:
        await client.close()


async def memory_context(task: str) -> Dict[str, Any]:
    """
    Retorna contexto relevante para uma task.

    Combines all 6 MIRIX memory types to provide comprehensive context.

    Args:
        task: Task description

    Returns:
        Context dict with memories from all types

    Example:
        >>> context = await memory_context("write integration tests")
        >>> context["procedural"]  # Skills related to testing
        [...]
    """
    from clients.memory_client import MemoryClient
    from config import get_config

    config = get_config()
    client = MemoryClient(config)

    try:
        result = await client.get_context_for_task(task)
        return result
    finally:
        await client.close()
