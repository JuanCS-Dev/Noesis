"""
MAXIMUS 2.0 - Memory Models
===========================

Data models for memory client operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MemoryType(str, Enum):
    """Types of memories supported."""

    SEMANTIC = "semantic"       # Facts and concepts
    EPISODIC = "episodic"       # Events and experiences
    PROCEDURAL = "procedural"   # How-to knowledge
    REFLECTION = "reflection"   # Metacognitive insights


@dataclass
class MemoryEntry:
    """A single memory entry."""

    memory_id: str
    content: str
    memory_type: MemoryType
    importance: float = 0.5
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    embedding: Optional[List[float]] = None


@dataclass
class SearchResult:
    """Result of a memory search."""

    memories: List[MemoryEntry]
    total_found: int
    query_time_ms: float = 0.0
