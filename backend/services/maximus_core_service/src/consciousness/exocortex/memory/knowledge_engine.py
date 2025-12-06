"""
Knowledge Engine Module
=======================

Manages the "Deep Memory" (exocortex) capabilities of the Digital Daimon.
Implements the "Mnemosyne" pattern of loading external context into the LLM's
active window (Tier 1 Hot Cache).

Follows strict Code Constitution standards:
- Type hinting
- Explicit error handling
- Simplicity (Tier 1 implementation first)
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field

# --- Constants ---
VALID_EXTENSIONS = {'.md', '.txt', '.py', '.json'}
MAX_FILE_SIZE_BYTES = 10_000_000  # 10MB limit per file for safety
DEFAULT_KB_PATH = "knowledge_base"


# --- Data Structures ---
@dataclass
class Document:
    """Represents a loaded document from the knowledge base."""
    filename: str
    content: str
    size_bytes: int
    timestamp: float = field(default_factory=time.time)

    def format_for_prompt(self) -> str:
        """Formats the document for context injection."""
        return f"--- DOCUMENT: {self.filename} ---\n{self.content}\n"


@dataclass
class KnowledgeContext:
    """Represents the aggregated context ready for injection."""
    total_documents: int
    total_chars: int
    formatted_content: str
    load_timestamp: float = field(default_factory=time.time)

    def summary(self) -> str:
        return f"Loaded {self.total_documents} documents ({self.total_chars} chars) at {self.load_timestamp}"


# --- Core Engine ---
class KnowledgeEngine:
    """
    Manages loading, caching, and retrieving knowledge base documents.
    
    Attributes:
        kb_path: Path to the knowledge base directory.
        _cache: In-memory cache of the loaded context.
        _logger: Standard logger.
    """

    def __init__(self, kb_path_str: str = DEFAULT_KB_PATH):
        """
        Initialize the Knowledge Engine.
        Tries to resolve the path relative to CWD or parent directories (Project Root).
        """
        # Try current dir
        candidate = Path(kb_path_str).resolve()
        
        # Try finding it in parents (up to 3 levels)
        if not candidate.exists():
            cwd = Path.cwd()
            for i in range(3): 
                # Try ../knowledge_base, ../../knowledge_base
                parent_candidate = cwd.parents[i] / kb_path_str
                if parent_candidate.exists():
                    candidate = parent_candidate
                    break
        
        self.kb_path = candidate
        self._cache: Optional[KnowledgeContext] = None
        self._logger = logging.getLogger(__name__)

        if not self.kb_path.exists():
            self._logger.warning(f"Knowledge Base path does not exist (checked {kb_path_str} and parents): {self.kb_path}")

    def load_context(self, force_refresh: bool = False) -> KnowledgeContext:
        """
        Loads all valid documents from the knowledge base.
        
        Uses a simple in-memory cache strategy. If cache exists and not forced, returns it.
        
        Args:
            force_refresh: If True, bypasses cache and reloads from disk.
            
        Returns:
            KnowledgeContext object containing formatted string.
            
        Raises:
            IOError: If critical filesystem access fails.
        """
        if self._cache and not force_refresh:
            self._logger.debug("Returning cached context")
            return self._cache

        self._logger.info(f"Loading context from {self.kb_path}")
        
        if not self.kb_path.exists():
             # Fail soft: return empty context but log warning
            self._logger.warning("Knowledge Base directory missing during load.")
            return KnowledgeContext(0, 0, "No knowledge base found.")

        documents: List[Document] = []
        
        try:
            for file_path in self.kb_path.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in VALID_EXTENSIONS:
                    doc = self._read_file(file_path)
                    if doc:
                        documents.append(doc)
        except Exception as e:
            self._logger.error(f"Failed to walk knowledge base: {e}")
            raise IOError(f"Critical failure loading knowledge base: {e}")

        # Assemble Context
        full_text_parts = [doc.format_for_prompt() for doc in documents]
        full_text = "\n".join(full_text_parts)
        
        ctx = KnowledgeContext(
            total_documents=len(documents),
            total_chars=len(full_text),
            formatted_content=full_text
        )
        
        self._cache = ctx
        self._logger.info(ctx.summary())
        return ctx

    def _read_file(self, path: Path) -> Optional[Document]:
        """Reads a single file safely."""
        try:
            stat = path.stat()
            if stat.st_size > MAX_FILE_SIZE_BYTES:
                self._logger.warning(f"Skipping {path.name}: too large ({stat.st_size} bytes)")
                return None
            
            content = path.read_text(encoding='utf-8', errors='replace')
            return Document(
                filename=path.name,
                content=content,
                size_bytes=len(content)
            )
        except Exception as e:
            self._logger.error(f"Error reading {path.name}: {e}")
            return None


# --- Singleton / Dependency Injection Helper ---
_global_engine: Optional[KnowledgeEngine] = None

def get_knowledge_engine() -> KnowledgeEngine:
    """Singleton accessor for the Knowledge Engine."""
    global _global_engine
    if _global_engine is None:
        # In a real app, config would come from settings
        _global_engine = KnowledgeEngine()
    return _global_engine
