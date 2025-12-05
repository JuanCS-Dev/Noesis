"""
Context Builder: Multi-Type Memory Context
==========================================

Builds context combining all 6 MIRIX memory types for task execution.

Based on: MIRIX Active Retrieval Mechanism (arXiv:2507.07957)
Retrieval scoring: Stanford Generative Agents (recency + importance + relevance)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

from models.memory import Memory, MemoryType

if TYPE_CHECKING:
    from core.memory_store import MemoryStore


logger = logging.getLogger(__name__)


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
    Context combining all 6 MIRIX memory types.

    Attributes:
        core: Identity + user facts (always included)
        episodic: Recent relevant experiences
        semantic: Relevant knowledge/concepts
        procedural: Applicable workflows/skills
        resource: Referenced documents
        vault: High-confidence consolidated memories
        retrieval_scores: Score per retrieved memory
        task: Original task query
    """

    core: List[Memory] = field(default_factory=list)
    episodic: List[Memory] = field(default_factory=list)
    semantic: List[Memory] = field(default_factory=list)
    procedural: List[Memory] = field(default_factory=list)
    resource: List[Memory] = field(default_factory=list)
    vault: List[Memory] = field(default_factory=list)
    retrieval_scores: Dict[str, float] = field(default_factory=dict)
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

        return "\n\n".join(sections)

    def total_memories(self) -> int:
        """Return total number of memories in context."""
        return (
            len(self.core) +
            len(self.episodic) +
            len(self.semantic) +
            len(self.procedural) +
            len(self.resource) +
            len(self.vault)
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
            "retrieval_scores": self.retrieval_scores,
            "total_memories": self.total_memories(),
        }


class ContextBuilder:  # pylint: disable=too-few-public-methods
    """
    Builds multi-type memory context for tasks.

    Based on: MIRIX Active Retrieval Mechanism.
    Uses keyword matching for now, extensible to vector search.
    """

    def __init__(
        self,
        memory_store: "MemoryStore",
        top_k: Optional[Dict[MemoryType, int]] = None
    ) -> None:
        """
        Initialize context builder.

        Args:
            memory_store: Memory store instance
            top_k: Optional custom top-K per type (defaults to DEFAULT_TOP_K)
        """
        self.store = memory_store
        self.top_k = top_k or DEFAULT_TOP_K.copy()

    async def get_context_for_task(self, task: str) -> MemoryContext:
        """
        Build context combining all 6 MIRIX memory types.

        Pipeline:
        1. Extract keywords from task
        2. Search each memory type (keyword match + importance sort)
        3. Compute retrieval scores
        4. Return combined MemoryContext

        Args:
            task: Task description

        Returns:
            MemoryContext with memories from all 6 types

        Example:
            >>> context = await builder.get_context_for_task("write unit tests")
            >>> len(context.procedural)
            5
        """
        keywords = self._extract_keywords(task)
        results: Dict[MemoryType, List[Memory]] = {}
        scores: Dict[str, float] = {}

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

        # Build context
        context = MemoryContext(
            core=results.get(MemoryType.CORE, []),
            episodic=results.get(MemoryType.EPISODIC, []),
            semantic=results.get(MemoryType.SEMANTIC, []),
            procedural=results.get(MemoryType.PROCEDURAL, []),
            resource=results.get(MemoryType.RESOURCE, []),
            vault=results.get(MemoryType.VAULT, []),
            retrieval_scores=scores,
            task=task,
        )

        logger.info(
            "Built context for task '%s': %d memories",
            task[:50], context.total_memories()
        )
        return context

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
