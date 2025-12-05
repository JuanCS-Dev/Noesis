"""
Episodic Memory: Memory Models
==============================

Data models for the episodic memory service.
Defines the structure for storing and retrieving agent memories.

Based on MIRIX 6-type architecture (arXiv:2507.07957, July 2025).
"""

from __future__ import annotations

from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """
    MIRIX 6-type memory architecture.

    Based on: https://arxiv.org/html/2507.07957v1 (July 2025)
    """

    CORE = "core"              # Persona + user facts (permanent)
    EPISODIC = "episodic"      # Time-stamped events (90 days TTL)
    SEMANTIC = "semantic"      # Knowledge/concepts (indefinite)
    PROCEDURAL = "procedural"  # Workflows/skills (indefinite)
    RESOURCE = "resource"      # External docs/media (30 days TTL)
    VAULT = "vault"            # Consolidated high-importance (indefinite)

    # Legacy aliases for backwards compatibility
    EXPERIENCE = "episodic"
    FACT = "semantic"
    PROCEDURE = "procedural"
    REFLECTION = "semantic"


# TTL configuration by type
MEMORY_TTL_DAYS: Dict[MemoryType, Optional[int]] = {
    MemoryType.CORE: None,        # Permanent
    MemoryType.EPISODIC: 90,      # 90 days
    MemoryType.SEMANTIC: None,    # Indefinite
    MemoryType.PROCEDURAL: None,  # Indefinite
    MemoryType.RESOURCE: 30,      # 30 days
    MemoryType.VAULT: None,       # Indefinite
}


class Memory(BaseModel):
    """
    A single unit of memory with MIRIX-compatible fields.

    Attributes:
        memory_id: Unique identifier
        type: MIRIX memory type
        content: The actual memory content (text or structured)
        context: Metadata about the memory (tags, source, etc.)
        embedding: Vector embedding for semantic search
        importance: Importance score (0.0-1.0), decays over time
        timestamp: When the memory was created
        access_count: Number of times this memory was retrieved
        last_accessed: Last retrieval timestamp
    """

    memory_id: str
    type: MemoryType
    content: str
    context: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    access_count: int = Field(default=0, ge=0)
    last_accessed: Optional[datetime] = None

    def record_access(self) -> None:
        """Record memory access for retrieval scoring."""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()

    def is_expired(self) -> bool:
        """Check if memory has expired based on TTL."""
        ttl = MEMORY_TTL_DAYS.get(self.type)
        if ttl is None:
            return False
        expiry = self.timestamp + timedelta(days=ttl)
        return datetime.utcnow() > expiry

    def get_recency_score(self, decay_factor: float = 0.995) -> float:
        """
        Compute recency score using Ebbinghaus decay.

        Formula: score = decay_factor ^ hours_elapsed
        Default decay: 0.995 (Stanford Generative Agents)

        Returns:
            Recency score between 0.0 and 1.0
        """
        hours = (datetime.utcnow() - self.timestamp).total_seconds() / 3600
        return decay_factor ** hours


class MemoryQuery(BaseModel):
    """
    Query to search for memories.

    Attributes:
        query_text: Natural language query
        type: Filter by memory type
        limit: Max number of results
        min_importance: Filter by importance
    """
    query_text: str
    type: Optional[MemoryType] = None
    limit: int = 5
    min_importance: float = 0.0


class MemorySearchResult(BaseModel):
    """
    Result of a memory search.

    Attributes:
        memories: List of matching memories
        total_found: Total number of matches
    """
    memories: List[Memory]
    total_found: int
