"""
Persistent Memory Store
=======================

Production-ready memory store with:
- Qdrant vector database for semantic search
- JSON file fallback for resilience
- Gemini embeddings generation
- Automatic persistence between restarts

Based on: MIRIX (arXiv:2507.07957) + Mem0 (arXiv:2504.19413)
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any

import google.generativeai as genai
from qdrant_client import QdrantClient as QdrantSDK
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from episodic_memory.models.memory import (
    Memory,
    MemoryQuery,
    MemorySearchResult,
    MemoryType,
)


logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generate embeddings using Gemini API.

    Uses text-embedding-004 model (768 dimensions).
    """

    EMBEDDING_MODEL = "models/text-embedding-004"
    VECTOR_SIZE = 768  # Gemini embedding size

    def __init__(self):
        """Initialize Gemini embeddings."""
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("No Gemini API key found - embeddings will be zero vectors")
            self._enabled = False
        else:
            genai.configure(api_key=api_key)
            self._enabled = True
            logger.info("Gemini embeddings initialized")

    def generate(self, text: str) -> List[float]:
        """Generate embedding for text."""
        if not self._enabled:
            return [0.0] * self.VECTOR_SIZE

        try:
            result = genai.embed_content(
                model=self.EMBEDDING_MODEL,
                content=text,
                task_type="retrieval_document"
            )
            return result["embedding"]
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return [0.0] * self.VECTOR_SIZE

    def generate_query(self, text: str) -> List[float]:
        """Generate embedding for query (different task type)."""
        if not self._enabled:
            return [0.0] * self.VECTOR_SIZE

        try:
            result = genai.embed_content(
                model=self.EMBEDDING_MODEL,
                content=text,
                task_type="retrieval_query"
            )
            return result["embedding"]
        except Exception as e:
            logger.error(f"Query embedding failed: {e}")
            return [0.0] * self.VECTOR_SIZE


class PersistentMemoryStore:
    """
    Production memory store with Qdrant + JSON fallback.

    Features:
    - Qdrant vector DB for semantic search
    - JSON file backup for resilience
    - Automatic embedding generation
    - L1 in-memory cache for hot data
    - Ebbinghaus decay + consolidation

    Architecture:
    - L1: In-memory dict (hot cache)
    - L2: Qdrant vector DB (persistent, semantic search)
    - L3: JSON file (backup, disaster recovery)
    """

    COLLECTION_NAME = "maximus_episodic_memory"

    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        data_dir: str = "data/memory",
        use_qdrant: bool = True
    ):
        """
        Initialize persistent store.

        Args:
            qdrant_url: Qdrant server URL
            data_dir: Directory for JSON backup
            use_qdrant: Whether to use Qdrant (False = JSON only)
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.backup_file = self.data_dir / "memories_backup.json"

        # L1: In-memory cache
        self._cache: Dict[str, Memory] = {}

        # Embedding generator
        self.embedder = EmbeddingGenerator()

        # Qdrant connection
        self.qdrant: Optional[QdrantSDK] = None
        self.qdrant_available = False

        if use_qdrant:
            try:
                self.qdrant = QdrantSDK(url=qdrant_url)
                self._ensure_collection()
                self.qdrant_available = True
                logger.info(f"Qdrant connected: {qdrant_url}")
            except Exception as e:
                logger.warning(f"Qdrant unavailable ({e}) - using JSON fallback")
                self.qdrant = None

        # Load backup into cache
        self._load_backup()

        logger.info(
            f"PersistentMemoryStore initialized: "
            f"qdrant={self.qdrant_available}, "
            f"cached={len(self._cache)}"
        )

    def _ensure_collection(self) -> None:
        """Create Qdrant collection if needed."""
        if not self.qdrant:
            return

        collections = self.qdrant.get_collections().collections
        names = [c.name for c in collections]

        if self.COLLECTION_NAME not in names:
            self.qdrant.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=EmbeddingGenerator.VECTOR_SIZE,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created Qdrant collection: {self.COLLECTION_NAME}")

    def _load_backup(self) -> None:
        """Load memories from JSON backup."""
        if not self.backup_file.exists():
            return

        try:
            with open(self.backup_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for mem_data in data.get("memories", []):
                memory = Memory(
                    memory_id=mem_data["memory_id"],
                    type=MemoryType(mem_data["type"]),
                    content=mem_data["content"],
                    context=mem_data.get("context", {}),
                    importance=mem_data.get("importance", 0.5),
                    timestamp=datetime.fromisoformat(mem_data["timestamp"]),
                    access_count=mem_data.get("access_count", 0),
                    last_accessed=(
                        datetime.fromisoformat(mem_data["last_accessed"])
                        if mem_data.get("last_accessed")
                        else None
                    )
                )
                self._cache[memory.memory_id] = memory

            logger.info(f"Loaded {len(self._cache)} memories from backup")
        except Exception as e:
            logger.error(f"Failed to load backup: {e}")

    def _save_backup(self) -> None:
        """Save memories to JSON backup."""
        try:
            memories_data = []
            for memory in self._cache.values():
                memories_data.append({
                    "memory_id": memory.memory_id,
                    "type": memory.type.value,
                    "content": memory.content,
                    "context": memory.context,
                    "importance": memory.importance,
                    "timestamp": memory.timestamp.isoformat(),
                    "access_count": memory.access_count,
                    "last_accessed": (
                        memory.last_accessed.isoformat()
                        if memory.last_accessed
                        else None
                    )
                })

            with open(self.backup_file, "w", encoding="utf-8") as f:
                json.dump({
                    "version": "1.0",
                    "saved_at": datetime.utcnow().isoformat(),
                    "count": len(memories_data),
                    "memories": memories_data
                }, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved {len(memories_data)} memories to backup")
        except Exception as e:
            logger.error(f"Failed to save backup: {e}")

    async def store(
        self,
        content: str,
        memory_type: MemoryType,
        context: Optional[Dict[str, Any]] = None,
        importance: float = 0.5
    ) -> Memory:
        """
        Store a new memory with persistence.

        Args:
            content: Memory content
            memory_type: MIRIX type
            context: Optional metadata
            importance: Importance score (0-1)

        Returns:
            Created Memory object
        """
        memory_id = str(uuid.uuid4())
        memory = Memory(
            memory_id=memory_id,
            type=memory_type,
            content=content,
            context=context or {},
            importance=importance,
            timestamp=datetime.utcnow()
        )

        # Generate embedding
        embedding = self.embedder.generate(content)
        memory.embedding = embedding

        # Store in L1 cache
        self._cache[memory_id] = memory

        # Store in Qdrant
        if self.qdrant and self.qdrant_available:
            try:
                self.qdrant.upsert(
                    collection_name=self.COLLECTION_NAME,
                    points=[
                        PointStruct(
                            id=memory_id,
                            vector=embedding,
                            payload={
                                "type": memory_type.value,
                                "content": content,
                                "context": context or {},
                                "importance": importance,
                                "timestamp": memory.timestamp.isoformat(),
                                "access_count": 0
                            }
                        )
                    ]
                )
            except Exception as e:
                logger.error(f"Qdrant store failed: {e}")

        # Backup to JSON
        self._save_backup()

        logger.info(f"Stored memory: {memory_id[:8]} (type={memory_type.value})")
        return memory

    async def retrieve(self, query: MemoryQuery) -> MemorySearchResult:
        """
        Retrieve memories using semantic search.

        Args:
            query: Search criteria

        Returns:
            Search results with matching memories
        """
        # Try Qdrant semantic search first
        if self.qdrant and self.qdrant_available and self.embedder._enabled:
            try:
                query_embedding = self.embedder.generate_query(query.query_text)

                # Build filter
                qdrant_filter = None
                if query.type:
                    qdrant_filter = Filter(
                        must=[
                            FieldCondition(
                                key="type",
                                match=MatchValue(value=query.type.value)
                            )
                        ]
                    )

                results = self.qdrant.search(
                    collection_name=self.COLLECTION_NAME,
                    query_vector=query_embedding,
                    limit=query.limit * 2,  # Fetch extra for filtering
                    query_filter=qdrant_filter,
                    score_threshold=0.5
                )

                memories = []
                for result in results:
                    payload = result.payload

                    # Filter by importance
                    if payload.get("importance", 0) < query.min_importance:
                        continue

                    memory = Memory(
                        memory_id=str(result.id),
                        type=MemoryType(payload["type"]),
                        content=payload["content"],
                        context=payload.get("context", {}),
                        importance=payload.get("importance", 0.5),
                        timestamp=datetime.fromisoformat(payload["timestamp"]),
                        access_count=payload.get("access_count", 0)
                    )
                    memory.record_access()
                    memories.append(memory)

                    # Update cache
                    self._cache[memory.memory_id] = memory

                    if len(memories) >= query.limit:
                        break

                if memories:
                    logger.debug(f"Qdrant search returned {len(memories)} results")
                    return MemorySearchResult(
                        memories=memories,
                        total_found=len(memories)
                    )
            except Exception as e:
                logger.warning(f"Qdrant search failed ({e}), falling back to cache")

        # Fallback: keyword search in cache
        results: List[Memory] = []
        query_terms = query.query_text.lower().split()

        for memory in self._cache.values():
            if query.type and memory.type != query.type:
                continue
            if memory.importance < query.min_importance:
                continue

            content_lower = memory.content.lower()
            if any(term in content_lower for term in query_terms):
                memory.record_access()
                results.append(memory)

        results.sort(key=lambda x: x.importance, reverse=True)
        limited = results[:query.limit]

        return MemorySearchResult(
            memories=limited,
            total_found=len(results)
        )

    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get memory by ID."""
        memory = self._cache.get(memory_id)
        if memory:
            memory.record_access()
        return memory

    async def delete(self, memory_id: str) -> bool:
        """Delete memory from all layers."""
        deleted = False

        # Remove from cache
        if memory_id in self._cache:
            del self._cache[memory_id]
            deleted = True

        # Remove from Qdrant
        if self.qdrant and self.qdrant_available:
            try:
                self.qdrant.delete(
                    collection_name=self.COLLECTION_NAME,
                    points_selector=[memory_id]
                )
            except Exception as e:
                logger.error(f"Qdrant delete failed: {e}")

        # Update backup
        if deleted:
            self._save_backup()

        return deleted

    async def consolidate_to_vault(
        self,
        threshold: float = 0.8,
        min_age_days: int = 7,
        min_access_count: int = 2
    ) -> Dict[str, int]:
        """Consolidate important memories to vault."""
        consolidated: Dict[str, int] = defaultdict(int)
        cutoff = datetime.utcnow() - timedelta(days=min_age_days)

        for memory in list(self._cache.values()):
            if memory.type in [MemoryType.VAULT, MemoryType.CORE]:
                continue

            if (memory.importance >= threshold and
                memory.timestamp < cutoff and
                memory.access_count >= min_access_count):

                original_type = memory.type.value
                memory.type = MemoryType.VAULT
                memory.context["original_type"] = original_type
                memory.context["consolidated_at"] = datetime.utcnow().isoformat()
                consolidated[original_type] += 1

        if sum(consolidated.values()) > 0:
            self._save_backup()

        return dict(consolidated)

    async def decay_importance(
        self,
        decay_factor: float = 0.995,
        boost_recent_access: bool = True,
        delete_threshold: float = 0.05
    ) -> Dict[str, int]:
        """Apply Ebbinghaus decay."""
        stats = {"decayed": 0, "boosted": 0, "deleted": 0}
        now = datetime.utcnow()
        to_delete = []

        for memory_id, memory in self._cache.items():
            if memory.type in [MemoryType.VAULT, MemoryType.CORE]:
                continue

            hours = (now - memory.timestamp).total_seconds() / 3600
            decayed = memory.importance * (decay_factor ** hours)

            if boost_recent_access and memory.last_accessed:
                hours_since = (now - memory.last_accessed).total_seconds() / 3600
                if hours_since < 24:
                    boost = 0.1 * (1 - hours_since / 24)
                    decayed = min(1.0, decayed + boost)
                    stats["boosted"] += 1

            memory.importance = decayed
            stats["decayed"] += 1

            if decayed < delete_threshold:
                to_delete.append(memory_id)

        for memory_id in to_delete:
            await self.delete(memory_id)
            stats["deleted"] += 1

        if stats["decayed"] > 0:
            self._save_backup()

        return stats

    async def get_memories_by_type(
        self,
        memory_type: MemoryType,
        limit: int = 10
    ) -> List[Memory]:
        """Get memories by type."""
        memories = [m for m in self._cache.values() if m.type == memory_type]
        memories.sort(key=lambda m: m.importance, reverse=True)
        return memories[:limit]

    async def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        type_counts: Dict[str, int] = defaultdict(int)
        total_importance = 0.0

        for memory in self._cache.values():
            type_counts[memory.type.value] += 1
            total_importance += memory.importance

        total = len(self._cache)

        return {
            "total_memories": total,
            "by_type": dict(type_counts),
            "avg_importance": total_importance / total if total > 0 else 0.0,
            "qdrant_available": self.qdrant_available,
            "embeddings_enabled": self.embedder._enabled
        }

    async def sync_to_qdrant(self) -> int:
        """Sync all cached memories to Qdrant (for recovery)."""
        if not self.qdrant or not self.qdrant_available:
            return 0

        synced = 0
        for memory in self._cache.values():
            try:
                if not memory.embedding:
                    memory.embedding = self.embedder.generate(memory.content)

                self.qdrant.upsert(
                    collection_name=self.COLLECTION_NAME,
                    points=[
                        PointStruct(
                            id=memory.memory_id,
                            vector=memory.embedding,
                            payload={
                                "type": memory.type.value,
                                "content": memory.content,
                                "context": memory.context,
                                "importance": memory.importance,
                                "timestamp": memory.timestamp.isoformat(),
                                "access_count": memory.access_count
                            }
                        )
                    ]
                )
                synced += 1
            except Exception as e:
                logger.error(f"Sync failed for {memory.memory_id}: {e}")

        logger.info(f"Synced {synced} memories to Qdrant")
        return synced
