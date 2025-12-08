"""
NOESIS Entity Index - Associative Memory Connections
=====================================================

Extracts entities from text and creates an inverted index for finding
related memories. Enables "memory association" - when searching for
one concept, related memories are found through shared entities.

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                    ENTITY INDEX                             │
    ├─────────────────────────────────────────────────────────────┤
    │  EXTRACTOR    │ Regex + heuristics (no external deps)      │
    │  INDEX        │ Dict[entity] -> Set[memory_id]             │
    │  STORAGE      │ JSON persistence in vault                  │
    └─────────────────────────────────────────────────────────────┘

Example:
    memory_1: "Juan é o criador do Noesis"
      -> entities: ["Juan", "criador", "Noesis"]
    
    memory_2: "O criador quer melhorar a memória"
      -> entities: ["criador", "memória"]
    
    index["criador"] = {memory_1, memory_2}  # CONNECTION!

Based on:
- Entity linking in knowledge graphs
- Inverted index for information retrieval
- Mem0 graph-based memory representations
"""

from __future__ import annotations

import json
import logging
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# Default storage path
ENTITY_INDEX_PATH = "/tmp/noesis/entity_index.json"

# Common Portuguese and English stopwords to ignore
STOPWORDS = {
    # Portuguese
    "a", "o", "e", "é", "de", "da", "do", "em", "na", "no", "um", "uma",
    "que", "para", "com", "por", "como", "mais", "mas", "foi", "ser",
    "está", "são", "tem", "ter", "seu", "sua", "isso", "esse", "essa",
    "este", "esta", "entre", "quando", "muito", "nos", "já", "eu", "ele",
    "ela", "você", "nós", "eles", "meu", "minha", "seu", "sua", "nosso",
    "nossa", "mesmo", "também", "pode", "fazer", "sobre", "depois", "então",
    # English
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "to", "of", "in",
    "for", "on", "with", "at", "by", "from", "as", "into", "through",
    "during", "before", "after", "above", "below", "between", "under",
    "again", "further", "then", "once", "here", "there", "when", "where",
    "why", "how", "all", "each", "few", "more", "most", "other", "some",
    "such", "no", "nor", "not", "only", "own", "same", "so", "than",
    "too", "very", "just", "and", "but", "if", "or", "because", "until",
    "while", "this", "that", "these", "those", "i", "you", "he", "she",
    "it", "we", "they", "my", "your", "his", "her", "its", "our", "their",
}

# Technical terms to always extract (Noesis-specific)
TECHNICAL_TERMS = {
    "noesis", "kuramoto", "esgt", "tribunal", "veritas", "sophia", "dikē", "dike",
    "consciência", "consciousness", "memória", "memory", "oscilador", "oscillator",
    "coerência", "coherence", "llm", "nebius", "gemini", "mnemosyne", "exocortex",
    "florescimento", "flourishing", "soul", "alma", "truth", "verdade", "wisdom",
    "sabedoria", "justice", "justiça", "criador", "creator", "juan",
}


@dataclass
class EntityMatch:
    """A matched entity with metadata."""
    entity: str
    original_text: str  # Original form in text
    entity_type: str    # "proper_noun", "technical", "keyword"
    start_pos: int
    end_pos: int


class EntityExtractor:
    """
    Extracts entities from text using regex and heuristics.
    
    No external dependencies (no spaCy, no NLTK).
    
    Extraction strategies:
    1. Capitalized words (proper nouns)
    2. Technical terms (Noesis-specific vocabulary)
    3. Quoted strings
    4. Numbers and dates
    5. Important keywords (nouns > 4 chars, not stopwords)
    """
    
    def __init__(
        self,
        min_word_length: int = 4,
        include_technical: bool = True,
        custom_terms: Optional[Set[str]] = None
    ):
        """
        Initialize entity extractor.
        
        Args:
            min_word_length: Minimum length for keyword extraction
            include_technical: Include Noesis-specific technical terms
            custom_terms: Additional custom terms to always extract
        """
        self.min_word_length = min_word_length
        self.technical_terms = TECHNICAL_TERMS.copy() if include_technical else set()
        if custom_terms:
            self.technical_terms.update(custom_terms)
        
        # Compile regex patterns
        self._patterns = {
            # Capitalized words (proper nouns) - but not at sentence start
            "proper_noun": re.compile(r'(?<=[.!?\s])\s*([A-Z][a-zà-ü]+(?:\s+[A-Z][a-zà-ü]+)*)'),
            # Quoted strings
            "quoted": re.compile(r'["\']([^"\']{2,50})["\']'),
            # Numbers and dates
            "numeric": re.compile(r'\b(\d{1,4}[/-]\d{1,2}[/-]\d{1,4}|\d+(?:\.\d+)?%?)\b'),
            # Technical terms (case insensitive)
            "technical": re.compile(
                r'\b(' + '|'.join(re.escape(t) for t in self.technical_terms) + r')\b',
                re.IGNORECASE
            ) if self.technical_terms else None,
        }
    
    def extract(self, text: str) -> List[str]:
        """
        Extract entities from text.
        
        Args:
            text: Input text
            
        Returns:
            List of unique entities (normalized to lowercase)
        """
        if not text or not text.strip():
            return []
        
        entities: Set[str] = set()
        
        # 1. Extract proper nouns (capitalized words)
        for match in self._patterns["proper_noun"].finditer(text):
            entity = match.group(1).strip()
            if len(entity) >= 2 and entity.lower() not in STOPWORDS:
                entities.add(entity.lower())
        
        # 2. Extract quoted strings
        for match in self._patterns["quoted"].finditer(text):
            entity = match.group(1).strip()
            if len(entity) >= 2:
                # Add the whole quoted phrase as one entity
                entities.add(entity.lower())
        
        # 3. Extract technical terms
        if self._patterns["technical"]:
            for match in self._patterns["technical"].finditer(text):
                entities.add(match.group(1).lower())
        
        # 4. Extract important keywords (long words, not stopwords)
        words = re.findall(r'\b[a-zA-Zà-üÀ-Ü]+\b', text)
        for word in words:
            word_lower = word.lower()
            if (len(word) >= self.min_word_length and 
                word_lower not in STOPWORDS and
                word_lower not in entities):  # Avoid duplicates
                entities.add(word_lower)
        
        return list(entities)
    
    def extract_with_metadata(self, text: str) -> List[EntityMatch]:
        """
        Extract entities with position and type metadata.
        
        Args:
            text: Input text
            
        Returns:
            List of EntityMatch objects with full metadata
        """
        matches: List[EntityMatch] = []
        seen: Set[str] = set()
        
        # Technical terms (highest priority)
        if self._patterns["technical"]:
            for match in self._patterns["technical"].finditer(text):
                entity = match.group(1).lower()
                if entity not in seen:
                    seen.add(entity)
                    matches.append(EntityMatch(
                        entity=entity,
                        original_text=match.group(1),
                        entity_type="technical",
                        start_pos=match.start(),
                        end_pos=match.end()
                    ))
        
        # Proper nouns
        for match in self._patterns["proper_noun"].finditer(text):
            entity = match.group(1).strip().lower()
            if entity not in seen and len(entity) >= 2 and entity not in STOPWORDS:
                seen.add(entity)
                matches.append(EntityMatch(
                    entity=entity,
                    original_text=match.group(1),
                    entity_type="proper_noun",
                    start_pos=match.start(),
                    end_pos=match.end()
                ))
        
        # Quoted strings
        for match in self._patterns["quoted"].finditer(text):
            entity = match.group(1).strip().lower()
            if entity not in seen:
                seen.add(entity)
                matches.append(EntityMatch(
                    entity=entity,
                    original_text=match.group(1),
                    entity_type="quoted",
                    start_pos=match.start(),
                    end_pos=match.end()
                ))
        
        return matches


@dataclass
class EntityIndex:
    """
    Inverted index mapping entities to memory IDs.
    
    Enables finding related memories through shared entities.
    
    Usage:
        index = EntityIndex()
        
        # Add memories
        index.add_memory("mem_1", ["juan", "criador", "noesis"])
        index.add_memory("mem_2", ["criador", "memoria"])
        
        # Find related
        related = index.get_related_memories(["criador"])
        # Returns: ["mem_1", "mem_2"]
    """
    
    # Entity -> Set of memory IDs
    _index: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    
    # Memory ID -> Set of entities (reverse lookup)
    _reverse: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    
    # Statistics
    _stats: Dict[str, int] = field(default_factory=lambda: {
        "total_entities": 0,
        "total_memories": 0,
        "total_connections": 0,
    })
    
    def add_memory(self, memory_id: str, entities: List[str]) -> int:
        """
        Add memory to index with its entities.
        
        Args:
            memory_id: Unique memory identifier
            entities: List of entities in this memory
            
        Returns:
            Number of entities indexed
        """
        if not entities:
            return 0
        
        # Normalize entities
        normalized = [e.lower().strip() for e in entities if e and len(e) >= 2]
        
        added = 0
        for entity in normalized:
            if memory_id not in self._index[entity]:
                self._index[entity].add(memory_id)
                self._reverse[memory_id].add(entity)
                added += 1
        
        # Update stats
        self._stats["total_entities"] = len(self._index)
        self._stats["total_memories"] = len(self._reverse)
        self._stats["total_connections"] = sum(len(v) for v in self._index.values())
        
        logger.debug(f"Indexed {added} entities for memory {memory_id[:8]}")
        return added
    
    def remove_memory(self, memory_id: str) -> int:
        """
        Remove memory from index.
        
        Args:
            memory_id: Memory to remove
            
        Returns:
            Number of entity associations removed
        """
        if memory_id not in self._reverse:
            return 0
        
        removed = 0
        entities = self._reverse[memory_id].copy()
        
        for entity in entities:
            if memory_id in self._index[entity]:
                self._index[entity].discard(memory_id)
                removed += 1
                # Clean up empty entries
                if not self._index[entity]:
                    del self._index[entity]
        
        del self._reverse[memory_id]
        
        # Update stats
        self._stats["total_entities"] = len(self._index)
        self._stats["total_memories"] = len(self._reverse)
        self._stats["total_connections"] = sum(len(v) for v in self._index.values())
        
        return removed
    
    def get_memories_for_entity(self, entity: str) -> List[str]:
        """Get all memory IDs containing an entity."""
        return list(self._index.get(entity.lower(), set()))
    
    def get_entities_for_memory(self, memory_id: str) -> List[str]:
        """Get all entities in a memory."""
        return list(self._reverse.get(memory_id, set()))
    
    def get_related_memories(
        self,
        entities: List[str],
        exclude_ids: Optional[Set[str]] = None,
        min_overlap: int = 1
    ) -> List[Tuple[str, int]]:
        """
        Find memories related to given entities.
        
        Args:
            entities: Entities to search for
            exclude_ids: Memory IDs to exclude from results
            min_overlap: Minimum entity overlap required
            
        Returns:
            List of (memory_id, overlap_count) sorted by overlap descending
        """
        exclude_ids = exclude_ids or set()
        memory_scores: Dict[str, int] = defaultdict(int)
        
        for entity in entities:
            entity_lower = entity.lower()
            for memory_id in self._index.get(entity_lower, set()):
                if memory_id not in exclude_ids:
                    memory_scores[memory_id] += 1
        
        # Filter by minimum overlap and sort
        results = [
            (mem_id, score) 
            for mem_id, score in memory_scores.items() 
            if score >= min_overlap
        ]
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
    
    def get_connections(
        self,
        memory_id: str,
        max_results: int = 10
    ) -> List[Tuple[str, List[str]]]:
        """
        Find memories connected to a given memory through shared entities.
        
        Args:
            memory_id: Memory to find connections for
            max_results: Maximum connections to return
            
        Returns:
            List of (connected_memory_id, shared_entities)
        """
        my_entities = self._reverse.get(memory_id, set())
        if not my_entities:
            return []
        
        # Find memories that share entities
        connections: Dict[str, Set[str]] = defaultdict(set)
        
        for entity in my_entities:
            for other_id in self._index.get(entity, set()):
                if other_id != memory_id:
                    connections[other_id].add(entity)
        
        # Sort by number of shared entities
        results = [
            (mem_id, list(shared))
            for mem_id, shared in connections.items()
        ]
        results.sort(key=lambda x: len(x[1]), reverse=True)
        
        return results[:max_results]
    
    def get_stats(self) -> Dict[str, int]:
        """Get index statistics."""
        return self._stats.copy()
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "index": {k: list(v) for k, v in self._index.items()},
            "reverse": {k: list(v) for k, v in self._reverse.items()},
            "stats": self._stats,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "EntityIndex":
        """Deserialize from dictionary."""
        instance = cls()
        
        index_data = data.get("index", {})
        for entity, memory_ids in index_data.items():
            instance._index[entity] = set(memory_ids)
        
        reverse_data = data.get("reverse", {})
        for memory_id, entities in reverse_data.items():
            instance._reverse[memory_id] = set(entities)
        
        instance._stats = data.get("stats", {
            "total_entities": len(instance._index),
            "total_memories": len(instance._reverse),
            "total_connections": sum(len(v) for v in instance._index.values()),
        })
        
        return instance
    
    def save_to_disk(self, filepath: str = ENTITY_INDEX_PATH) -> str:
        """Save index to disk."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"EntityIndex saved: {self._stats['total_entities']} entities, "
                   f"{self._stats['total_memories']} memories")
        return filepath
    
    @classmethod
    def load_from_disk(cls, filepath: str = ENTITY_INDEX_PATH) -> Optional["EntityIndex"]:
        """Load index from disk."""
        if not os.path.exists(filepath):
            logger.debug(f"EntityIndex file not found: {filepath}")
            return None
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            instance = cls.from_dict(data)
            logger.info(f"EntityIndex loaded: {instance._stats['total_entities']} entities")
            return instance
            
        except Exception as e:
            logger.error(f"Failed to load EntityIndex: {e}")
            return None
    
    def __len__(self) -> int:
        """Return number of unique entities."""
        return len(self._index)
    
    def __repr__(self) -> str:
        return f"EntityIndex(entities={len(self._index)}, memories={len(self._reverse)})"


# Singleton instances
_extractor: Optional[EntityExtractor] = None
_index: Optional[EntityIndex] = None


def get_entity_extractor() -> EntityExtractor:
    """Get or create singleton entity extractor."""
    global _extractor
    if _extractor is None:
        _extractor = EntityExtractor()
    return _extractor


def get_entity_index() -> EntityIndex:
    """Get or create singleton entity index (loads from disk if available)."""
    global _index
    if _index is None:
        _index = EntityIndex.load_from_disk() or EntityIndex()
    return _index


def extract_and_index(memory_id: str, content: str) -> List[str]:
    """
    Convenience function to extract entities and add to index.
    
    Args:
        memory_id: Memory identifier
        content: Memory content text
        
    Returns:
        List of extracted entities
    """
    extractor = get_entity_extractor()
    index = get_entity_index()
    
    entities = extractor.extract(content)
    index.add_memory(memory_id, entities)
    
    return entities

