"""
MIRIX-Inspired 6-Type Memory System
====================================

Memory architecture based on MIRIX research (July 2025).

6 Memory Types:
- CORE: Persistent persona + user facts
- EPISODIC: Time-stamped events (what/where/when)
- SEMANTIC: Knowledge graphs + concepts
- PROCEDURAL: Workflows + skills (how-to)
- RESOURCE: External docs/media (multimodal)
- VAULT: Sensitive data (encrypted, access-controlled)
"""

from __future__ import annotations

from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """
    6 types of memory (MIRIX architecture).

    Based on research: https://arxiv.org/MIRIX (July 2025)
    """

    CORE = "core"              # Persona + user facts (permanent)
    EPISODIC = "episodic"      # Time-stamped events (90 days)
    SEMANTIC = "semantic"      # Knowledge graphs (indefinite)
    PROCEDURAL = "procedural"  # Workflows/skills (indefinite)
    RESOURCE = "resource"      # External docs/media (30 days)
    VAULT = "vault"            # Sensitive data (encrypted, indefinite)


class MemoryPriority(int, Enum):
    """Priority for memory retrieval caching."""

    LOW = 1        # Resource, rarely accessed
    MEDIUM = 2     # Episodic, occasional access
    HIGH = 3       # Semantic, Procedural (frequent)
    CRITICAL = 4   # Core, Vault (always hot)


class TypedMemory(BaseModel):
    """
    Memory with type-specific handling.

    Attributes:
        id: Unique memory identifier
        type: Memory type (MIRIX category)
        content: Memory content (flexible dict)
        embedding: Vector embedding (1536 dims for OpenAI)
        metadata: Additional metadata
        timestamp: Creation timestamp
        ttl_days: Time-to-live in days (None = indefinite)
        access_count: Number of retrievals (for cache optimization)
        last_accessed: Last access timestamp
        encrypted: Whether content is encrypted (Vault only)

    Example:
        >>> memory = TypedMemory(
        ...     id="core-user-name",
        ...     type=MemoryType.CORE,
        ...     content={"user_name": "Juan", "role": "Architect"},
        ...     embedding=[0.1, 0.2, ...],
        ...     metadata={"source": "user_profile"}
        ... )
    """

    id: str = Field(..., description="Unique memory identifier")
    type: MemoryType = Field(..., description="MIRIX memory type")
    content: Dict[str, Any] = Field(..., description="Memory content")
    embedding: List[float] = Field(..., description="Vector embedding")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Creation time")
    ttl_days: Optional[int] = Field(None, description="Time-to-live (days)")

    access_count: int = Field(0, description="Retrieval count")
    last_accessed: Optional[datetime] = Field(None, description="Last access time")

    encrypted: bool = Field(False, description="Content encrypted (Vault only)")

    def record_access(self) -> None:
        """Record memory access for cache optimization."""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()

    def is_expired(self) -> bool:
        """
        Check if memory has expired based on TTL.

        Returns:
            True if expired, False otherwise
        """
        if self.ttl_days is None:
            return False  # Indefinite

        expiry_date = self.timestamp + timedelta(days=self.ttl_days)
        return datetime.utcnow() > expiry_date

    def should_cache(self, access_threshold: int = 3) -> bool:
        """
        Determine if memory should be cached.

        Args:
            access_threshold: Minimum access count for caching

        Returns:
            True if should cache
        """
        # Critical types always cached
        if self.type in [MemoryType.CORE, MemoryType.VAULT]:
            return True

        # High-frequency access
        if self.access_count >= access_threshold:
            return True

        # Recent access
        if self.last_accessed:
            hours_since_access = (datetime.utcnow() - self.last_accessed).total_seconds() / 3600
            return hours_since_access < 24

        return False

    @classmethod
    def get_ttl_for_type(cls, memory_type: MemoryType) -> Optional[int]:
        """
        Get default TTL for memory type.

        Args:
            memory_type: Memory type

        Returns:
            TTL in days (None = indefinite)
        """
        ttl_map = {
            MemoryType.CORE: None,        # Permanent
            MemoryType.EPISODIC: 90,      # 90 days
            MemoryType.SEMANTIC: None,    # Indefinite
            MemoryType.PROCEDURAL: None,  # Indefinite
            MemoryType.RESOURCE: 30,      # 30 days
            MemoryType.VAULT: None        # Indefinite (encrypted)
        }
        return ttl_map[memory_type]

    @classmethod
    def get_priority_for_type(cls, memory_type: MemoryType) -> MemoryPriority:
        """
        Get cache priority for memory type.

        Args:
            memory_type: Memory type

        Returns:
            Memory priority
        """
        priority_map = {
            MemoryType.CORE: MemoryPriority.CRITICAL,
            MemoryType.VAULT: MemoryPriority.CRITICAL,
            MemoryType.SEMANTIC: MemoryPriority.HIGH,
            MemoryType.PROCEDURAL: MemoryPriority.HIGH,
            MemoryType.EPISODIC: MemoryPriority.MEDIUM,
            MemoryType.RESOURCE: MemoryPriority.LOW
        }
        return priority_map[memory_type]


class MemoryTypeConfig(BaseModel):
    """
    Configuration for memory type.

    Attributes:
        type: Memory type
        ttl_days: Default TTL
        priority: Cache priority
        replication_factor: Number of replicas (HA)
        encryption_required: Whether encryption is required
    """

    type: MemoryType
    ttl_days: Optional[int]
    priority: MemoryPriority
    replication_factor: int = Field(1, ge=1, le=3, description="Replication (1-3)")
    encryption_required: bool = False

    @classmethod
    def for_type(cls, memory_type: MemoryType) -> "MemoryTypeConfig":
        """
        Get configuration for memory type.

        Args:
            memory_type: Memory type

        Returns:
            Memory type configuration
        """
        configs = {
            MemoryType.CORE: cls(
                type=MemoryType.CORE,
                ttl_days=None,
                priority=MemoryPriority.CRITICAL,
                replication_factor=3,  # High availability
                encryption_required=False
            ),
            MemoryType.EPISODIC: cls(
                type=MemoryType.EPISODIC,
                ttl_days=90,
                priority=MemoryPriority.MEDIUM,
                replication_factor=2,
                encryption_required=False
            ),
            MemoryType.SEMANTIC: cls(
                type=MemoryType.SEMANTIC,
                ttl_days=None,
                priority=MemoryPriority.HIGH,
                replication_factor=2,
                encryption_required=False
            ),
            MemoryType.PROCEDURAL: cls(
                type=MemoryType.PROCEDURAL,
                ttl_days=None,
                priority=MemoryPriority.HIGH,
                replication_factor=2,
                encryption_required=False
            ),
            MemoryType.RESOURCE: cls(
                type=MemoryType.RESOURCE,
                ttl_days=30,
                priority=MemoryPriority.LOW,
                replication_factor=1,
                encryption_required=False
            ),
            MemoryType.VAULT: cls(
                type=MemoryType.VAULT,
                ttl_days=None,
                priority=MemoryPriority.CRITICAL,
                replication_factor=3,
                encryption_required=True  # Always encrypted
            )
        }
        return configs[memory_type]
