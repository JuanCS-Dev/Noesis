"""
Context Builder: Multi-Type Memory Context
==========================================

Builds context combining all 6 MIRIX memory types for task execution.
Now with entity-based associative retrieval for connected reasoning.

Based on: MIRIX Active Retrieval Mechanism (arXiv:2507.07957)
Retrieval scoring: Stanford Generative Agents (recency + importance + relevance)
Entity connections: Anthropic context patterns + Mem0 graph memory
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, TYPE_CHECKING

from episodic_memory.models.memory import Memory, MemoryType

if TYPE_CHECKING:
    from episodic_memory.core.memory_store import MemoryStore


logger = logging.getLogger(__name__)

# Lazy import entity index to avoid circular imports
_entity_extractor = None
_entity_index = None


def _get_entity_extractor():
    """Lazy load entity extractor."""
    global _entity_extractor
    if _entity_extractor is None:
        from episodic_memory.core.entity_index import EntityExtractor
        _entity_extractor = EntityExtractor()
    return _entity_extractor


def _get_entity_index():
    """Lazy load entity index."""
    global _entity_index
    if _entity_index is None:
        from episodic_memory.core.entity_index import EntityIndex
        _entity_index = EntityIndex.load_from_disk() or EntityIndex()
    return _entity_index


# Default top-K per memory type
DEFAULT_TOP_K: Dict[MemoryType, int] = {
    MemoryType.CORE: 5,        # Always include identity
    MemoryType.EPISODIC: 10,   # Recent experiences
    MemoryType.SEMANTIC: 8,    # Relevant knowledge
    MemoryType.PROCEDURAL: 5,  # Applicable skills
    MemoryType.RESOURCE: 3,    # Referenced docs
    MemoryType.VAULT: 5,       # High-confidence
}


@dataclass
class MemoryContext:  # pylint: disable=too-many-instance-attributes
    """
    Context combining all 6 MIRIX memory types + connected memories.

    Attributes:
        core: Identity + user facts (always included)
        episodic: Recent relevant experiences
        semantic: Relevant knowledge/concepts
        procedural: Applicable workflows/skills
        resource: Referenced documents
        vault: High-confidence consolidated memories
        connected: Memories connected via shared entities (associative)
        retrieval_scores: Score per retrieved memory
        entity_connections: Mapping of memory_id -> shared entities
        task: Original task query
    """

    core: List[Memory] = field(default_factory=list)
    episodic: List[Memory] = field(default_factory=list)
    semantic: List[Memory] = field(default_factory=list)
    procedural: List[Memory] = field(default_factory=list)
    resource: List[Memory] = field(default_factory=list)
    vault: List[Memory] = field(default_factory=list)
    connected: List[Memory] = field(default_factory=list)
    retrieval_scores: Dict[str, float] = field(default_factory=dict)
    entity_connections: Dict[str, List[str]] = field(default_factory=dict)
    task: str = ""

    def to_prompt_context(self) -> str:
        """
        Format memory context for LLM prompt injection.

        Returns:
            Formatted string with sections by memory type
        """
        sections: List[str] = []

        if self.core:
            core_content = "\n".join(f"- {m.content}" for m in self.core)
            sections.append(f"[CORE IDENTITY]\n{core_content}")

        if self.episodic:
            episodic_content = "\n".join(f"- {m.content}" for m in self.episodic)
            sections.append(f"[RECENT EXPERIENCES]\n{episodic_content}")

        if self.semantic:
            semantic_content = "\n".join(f"- {m.content}" for m in self.semantic)
            sections.append(f"[KNOWLEDGE]\n{semantic_content}")

        if self.procedural:
            procedural_content = "\n".join(f"- {m.content}" for m in self.procedural)
            sections.append(f"[SKILLS/WORKFLOWS]\n{procedural_content}")

        if self.resource:
            resource_content = "\n".join(f"- {m.content}" for m in self.resource)
            sections.append(f"[RESOURCES]\n{resource_content}")

        if self.vault:
            vault_content = "\n".join(f"- {m.content}" for m in self.vault)
            sections.append(f"[VAULT (HIGH CONFIDENCE)]\n{vault_content}")

        if self.connected:
            # Format connected memories with their shared entities
            connected_lines = []
            for m in self.connected:
                shared = self.entity_connections.get(m.memory_id, [])
                if shared:
                    connected_lines.append(f"- {m.content} (via: {', '.join(shared)})")
                else:
                    connected_lines.append(f"- {m.content}")
            sections.append(f"[CONNECTED (ASSOCIATED MEMORIES)]\n" + "\n".join(connected_lines))

        return "\n\n".join(sections)

    def total_memories(self) -> int:
        """Return total number of memories in context."""
        return (
            len(self.core) +
            len(self.episodic) +
            len(self.semantic) +
            len(self.procedural) +
            len(self.resource) +
            len(self.vault) +
            len(self.connected)
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary for API response."""
        return {
            "task": self.task,
            "core": [m.model_dump() for m in self.core],
            "episodic": [m.model_dump() for m in self.episodic],
            "semantic": [m.model_dump() for m in self.semantic],
            "procedural": [m.model_dump() for m in self.procedural],
            "resource": [m.model_dump() for m in self.resource],
            "vault": [m.model_dump() for m in self.vault],
            "connected": [m.model_dump() for m in self.connected],
            "retrieval_scores": self.retrieval_scores,
            "entity_connections": self.entity_connections,
            "total_memories": self.total_memories(),
        }


class ContextBuilder:  # pylint: disable=too-few-public-methods
    """
    Builds multi-type memory context for tasks.

    Based on: MIRIX Active Retrieval Mechanism.
    Uses keyword matching + entity-based associative retrieval.
    """

    def __init__(
        self,
        memory_store: "MemoryStore",
        top_k: Optional[Dict[MemoryType, int]] = None,
        max_connected: int = 5
    ) -> None:
        """
        Initialize context builder.

        Args:
            memory_store: Memory store instance
            top_k: Optional custom top-K per type (defaults to DEFAULT_TOP_K)
            max_connected: Maximum connected memories to retrieve
        """
        self.store = memory_store
        self.top_k = top_k or DEFAULT_TOP_K.copy()
        self.max_connected = max_connected

    async def get_context_for_task(self, task: str) -> MemoryContext:
        """
        Build context combining all 6 MIRIX memory types + connected memories.

        Pipeline:
        1. Extract keywords from task
        2. Extract entities from task (for associative retrieval)
        3. Search each memory type (keyword match + importance sort)
        4. Find connected memories via entity index
        5. Compute retrieval scores
        6. Return combined MemoryContext

        Args:
            task: Task description

        Returns:
            MemoryContext with memories from all 6 types + connections

        Example:
            >>> context = await builder.get_context_for_task("what did Juan say about memory?")
            >>> len(context.connected)  # Memories connected via "Juan" entity
            3
        """
        keywords = self._extract_keywords(task)
        results: Dict[MemoryType, List[Memory]] = {}
        scores: Dict[str, float] = {}
        
        # Extract entities from task for associative retrieval
        extractor = _get_entity_extractor()
        task_entities = extractor.extract(task)

        # Search each memory type
        for memory_type in MemoryType:
            # Skip legacy aliases
            if memory_type.value in ["experience", "fact", "procedure", "reflection"]:
                if memory_type not in [MemoryType.CORE, MemoryType.EPISODIC,
                                       MemoryType.SEMANTIC, MemoryType.PROCEDURAL,
                                       MemoryType.RESOURCE, MemoryType.VAULT]:
                    continue

            memories = await self._search_type(
                keywords,
                memory_type,
                self.top_k.get(memory_type, 5)
            )
            results[memory_type] = memories

            # Compute retrieval scores
            for mem in memories:
                scores[mem.memory_id] = self._compute_retrieval_score(mem, keywords)
                mem.record_access()  # Track access for decay boosting

        # Find connected memories via entity index
        connected_memories, entity_connections = await self._find_connected_memories(
            task_entities,
            results,
            scores
        )

        # Build context
        context = MemoryContext(
            core=results.get(MemoryType.CORE, []),
            episodic=results.get(MemoryType.EPISODIC, []),
            semantic=results.get(MemoryType.SEMANTIC, []),
            procedural=results.get(MemoryType.PROCEDURAL, []),
            resource=results.get(MemoryType.RESOURCE, []),
            vault=results.get(MemoryType.VAULT, []),
            connected=connected_memories,
            retrieval_scores=scores,
            entity_connections=entity_connections,
            task=task,
        )

        logger.info(
            "Built context for task '%s': %d memories (%d connected via entities)",
            task[:50], context.total_memories(), len(connected_memories)
        )
        return context
    
    async def _find_connected_memories(
        self,
        task_entities: List[str],
        direct_results: Dict[MemoryType, List[Memory]],
        scores: Dict[str, float]
    ) -> tuple[List[Memory], Dict[str, List[str]]]:
        """
        Find memories connected via shared entities.

        Args:
            task_entities: Entities extracted from task
            direct_results: Already retrieved memories (to exclude)
            scores: Scores dict to update

        Returns:
            Tuple of (connected_memories, entity_connections)
        """
        if not task_entities:
            return [], {}
        
        index = _get_entity_index()
        
        # Get IDs of already retrieved memories
        already_retrieved: Set[str] = set()
        for memories in direct_results.values():
            already_retrieved.update(m.memory_id for m in memories)
        
        # Find related memories via entity index
        related = index.get_related_memories(
            task_entities,
            exclude_ids=already_retrieved,
            min_overlap=1
        )
        
        connected_memories: List[Memory] = []
        entity_connections: Dict[str, List[str]] = {}
        
        for memory_id, overlap_count in related[:self.max_connected]:
            memory = self.store._storage.get(memory_id)  # pylint: disable=protected-access
            if memory:
                connected_memories.append(memory)
                # Find which entities connect this memory
                memory_entities = set(memory.context.get("entities", []))
                shared = list(memory_entities & set(task_entities))
                entity_connections[memory_id] = shared
                
                # Compute and store score
                base_score = 0.5 + (overlap_count * 0.1)  # Boost for entity overlap
                scores[memory_id] = min(1.0, base_score)
                memory.record_access()
        
        return connected_memories, entity_connections

    async def _search_type(
        self,
        keywords: List[str],
        memory_type: MemoryType,
        limit: int
    ) -> List[Memory]:
        """
        Search memories of a specific type.

        Uses keyword matching + importance sorting.
        Future: integrate with vector search.

        Args:
            keywords: Search keywords
            memory_type: Type to search
            limit: Max results

        Returns:
            Matching memories sorted by score
        """
        matches: List[tuple[Memory, float]] = []

        # pylint: disable=protected-access
        for memory in self.store._storage.values():
            if memory.type != memory_type:
                continue

            # Compute match score (keyword overlap)
            content_lower = memory.content.lower()
            match_count = sum(1 for kw in keywords if kw in content_lower)

            if match_count > 0:
                score = self._compute_retrieval_score(memory, keywords)
                matches.append((memory, score))

        # Sort by score descending
        matches.sort(key=lambda x: x[1], reverse=True)

        # Return top-K
        return [m for m, _ in matches[:limit]]

    def _compute_retrieval_score(
        self,
        memory: Memory,
        keywords: List[str]
    ) -> float:
        """
        Compute combined retrieval score.

        Formula (Stanford Generative Agents):
        score = 0.3 * recency + 0.3 * importance + 0.4 * relevance

        Args:
            memory: Memory to score
            keywords: Query keywords

        Returns:
            Combined score (0.0 - 1.0)
        """
        # Recency (Ebbinghaus decay)
        recency = memory.get_recency_score()

        # Importance (stored value)
        importance = memory.importance

        # Relevance (keyword overlap ratio)
        content_lower = memory.content.lower()
        match_count = sum(1 for kw in keywords if kw in content_lower)
        relevance = min(1.0, match_count / max(len(keywords), 1))

        return (0.3 * recency) + (0.3 * importance) + (0.4 * relevance)

    @staticmethod
    def _extract_keywords(task: str) -> List[str]:
        """
        Extract keywords from task description.

        Simple implementation: lowercase, split, filter stopwords.

        Args:
            task: Task description

        Returns:
            List of keywords
        """
        stopwords = {
            "a", "an", "the", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "shall",
            "can", "to", "of", "in", "for", "on", "with", "at", "by",
            "from", "as", "into", "through", "during", "before", "after",
            "above", "below", "between", "under", "again", "further",
            "then", "once", "here", "there", "when", "where", "why",
            "how", "all", "each", "few", "more", "most", "other", "some",
            "such", "no", "nor", "not", "only", "own", "same", "so",
            "than", "too", "very", "just", "and", "but", "if", "or",
            "because", "until", "while", "this", "that", "these", "those",
        }

        words = task.lower().split()
        keywords = [w for w in words if w not in stopwords and len(w) > 2]

        return keywords
