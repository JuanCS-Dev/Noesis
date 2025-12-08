"""
NOESIS Session Memory - Conversation Context Management
========================================================

Manages conversation history within a session, enabling coherent multi-turn
conversations. Implements sliding window + recursive summarization.

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                    SESSION MEMORY                           │
    ├─────────────────────────────────────────────────────────────┤
    │  BUFFER (recent turns)  │ Circular, max 20 turns           │
    │  SUMMARY (compressed)   │ LLM-generated summary of old     │
    │  PERSISTENCE            │ /tmp/noesis/session_*.json       │
    └─────────────────────────────────────────────────────────────┘

Based on:
- Sliding window context management
- Recursive summarization (Anthropic best practices)
- Stanford Generative Agents memory compression
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Callable, Awaitable
from uuid import uuid4

logger = logging.getLogger(__name__)

# Default paths
SESSION_DIR = "/tmp/noesis"
MAX_TURNS_BEFORE_SUMMARY = 10
MAX_BUFFER_SIZE = 20


@dataclass
class Turn:
    """A single conversation turn."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Turn":
        return cls(**data)
    
    def format_for_prompt(self) -> str:
        """Format turn for inclusion in prompt."""
        role_label = "User" if self.role == "user" else "Noesis"
        return f"{role_label}: {self.content}"


@dataclass
class SessionMemory:
    """
    Manages conversation memory within a session.
    
    Features:
    - Circular buffer for recent turns
    - Automatic summarization when buffer grows
    - Disk persistence for session recovery
    - Context formatting for LLM prompts
    
    Usage:
        session = SessionMemory()
        session.add_turn("user", "Hello, my name is Juan")
        session.add_turn("assistant", "Hello Juan! How can I help?")
        
        context = session.get_context()
        # Returns formatted conversation history
    """
    
    session_id: str = field(default_factory=lambda: str(uuid4())[:8])
    turns: List[Turn] = field(default_factory=list)
    summary: str = ""
    max_turns: int = MAX_BUFFER_SIZE
    summary_threshold: int = MAX_TURNS_BEFORE_SUMMARY
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Summarizer callback (set externally to avoid circular imports)
    _summarizer: Optional[Callable[[str], Awaitable[str]]] = field(
        default=None, repr=False, compare=False
    )
    
    def add_turn(self, role: str, content: str) -> None:
        """
        Add a conversation turn.
        
        Args:
            role: "user" or "assistant"
            content: Message content
        """
        turn = Turn(role=role, content=content)
        self.turns.append(turn)
        
        # Check if we need to compress old turns
        if len(self.turns) > self.max_turns:
            self._compress_old_turns()
        
        logger.debug(f"Session {self.session_id}: Added {role} turn ({len(self.turns)} total)")
    
    def _compress_old_turns(self) -> None:
        """Compress oldest turns into summary (sync version - uses simple concatenation)."""
        if len(self.turns) <= self.summary_threshold:
            return
        
        # Take oldest turns to summarize
        turns_to_compress = self.turns[:self.summary_threshold // 2]
        remaining_turns = self.turns[self.summary_threshold // 2:]
        
        # Simple compression: concatenate to existing summary
        compressed_text = "\n".join(t.format_for_prompt() for t in turns_to_compress)
        
        if self.summary:
            self.summary = f"{self.summary}\n\n[Earlier conversation continued:]\n{compressed_text}"
        else:
            self.summary = f"[Earlier in this conversation:]\n{compressed_text}"
        
        self.turns = remaining_turns
        logger.info(f"Session {self.session_id}: Compressed {len(turns_to_compress)} turns to summary")
    
    async def summarize_if_needed(self, summarizer: Callable[[str], Awaitable[str]]) -> None:
        """
        Use LLM to create intelligent summary when buffer is large.
        
        Args:
            summarizer: Async function that takes text and returns summary
        """
        if len(self.turns) <= self.summary_threshold:
            return
        
        # Take oldest turns to summarize
        turns_to_compress = self.turns[:self.summary_threshold // 2]
        remaining_turns = self.turns[self.summary_threshold // 2:]
        
        # Create text for summarization
        conversation_text = "\n".join(t.format_for_prompt() for t in turns_to_compress)
        
        # Use LLM to summarize
        try:
            summary_prompt = f"""Summarize this conversation excerpt in 2-3 sentences, 
preserving key facts, names, and context that might be referenced later:

{conversation_text}

Summary:"""
            
            new_summary = await summarizer(summary_prompt)
            
            if self.summary:
                self.summary = f"{self.summary}\n\n{new_summary}"
            else:
                self.summary = new_summary
            
            self.turns = remaining_turns
            logger.info(f"Session {self.session_id}: LLM-summarized {len(turns_to_compress)} turns")
            
        except Exception as e:
            logger.warning(f"LLM summarization failed, using simple compression: {e}")
            self._compress_old_turns()
    
    def get_context(self, last_n: Optional[int] = None) -> str:
        """
        Get formatted conversation context for prompt injection.
        
        Args:
            last_n: Only include last N turns (None = all)
            
        Returns:
            Formatted context string
        """
        parts = []
        
        # Add summary if exists
        if self.summary:
            parts.append(f"[CONVERSATION CONTEXT]\n{self.summary}")
        
        # Add recent turns
        turns_to_include = self.turns[-last_n:] if last_n else self.turns
        
        if turns_to_include:
            recent = "\n".join(t.format_for_prompt() for t in turns_to_include)
            if self.summary:
                parts.append(f"\n[RECENT CONVERSATION]\n{recent}")
            else:
                parts.append(f"[CONVERSATION HISTORY]\n{recent}")
        
        return "\n".join(parts) if parts else ""
    
    def get_last_user_message(self) -> Optional[str]:
        """Get the most recent user message."""
        for turn in reversed(self.turns):
            if turn.role == "user":
                return turn.content
        return None
    
    def get_last_assistant_message(self) -> Optional[str]:
        """Get the most recent assistant message."""
        for turn in reversed(self.turns):
            if turn.role == "assistant":
                return turn.content
        return None
    
    def clear(self) -> None:
        """Clear all conversation history."""
        self.turns = []
        self.summary = ""
        logger.info(f"Session {self.session_id}: Cleared")
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "session_id": self.session_id,
            "turns": [t.to_dict() for t in self.turns],
            "summary": self.summary,
            "created_at": self.created_at,
            "max_turns": self.max_turns,
            "summary_threshold": self.summary_threshold,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SessionMemory":
        """Deserialize from dictionary."""
        turns = [Turn.from_dict(t) for t in data.get("turns", [])]
        return cls(
            session_id=data.get("session_id", str(uuid4())[:8]),
            turns=turns,
            summary=data.get("summary", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
            max_turns=data.get("max_turns", MAX_BUFFER_SIZE),
            summary_threshold=data.get("summary_threshold", MAX_TURNS_BEFORE_SUMMARY),
        )
    
    def save_to_disk(self, directory: str = SESSION_DIR) -> str:
        """
        Save session to disk for persistence.
        
        Args:
            directory: Directory to save session file
            
        Returns:
            Path to saved file
        """
        Path(directory).mkdir(parents=True, exist_ok=True)
        filepath = os.path.join(directory, f"session_{self.session_id}.json")
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.debug(f"Session {self.session_id}: Saved to {filepath}")
        return filepath
    
    @classmethod
    def load_from_disk(cls, session_id: str, directory: str = SESSION_DIR) -> Optional["SessionMemory"]:
        """
        Load session from disk.
        
        Args:
            session_id: Session ID to load
            directory: Directory containing session files
            
        Returns:
            SessionMemory instance or None if not found
        """
        filepath = os.path.join(directory, f"session_{session_id}.json")
        
        if not os.path.exists(filepath):
            logger.debug(f"Session file not found: {filepath}")
            return None
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            session = cls.from_dict(data)
            logger.info(f"Session {session_id}: Loaded from disk ({len(session.turns)} turns)")
            return session
            
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None
    
    @classmethod
    def list_sessions(cls, directory: str = SESSION_DIR) -> List[str]:
        """List all saved session IDs."""
        if not os.path.exists(directory):
            return []
        
        sessions = []
        for filename in os.listdir(directory):
            if filename.startswith("session_") and filename.endswith(".json"):
                session_id = filename[8:-5]  # Remove "session_" and ".json"
                sessions.append(session_id)
        
        return sessions
    
    def __len__(self) -> int:
        """Return number of turns in buffer."""
        return len(self.turns)
    
    def __repr__(self) -> str:
        return f"SessionMemory(id={self.session_id}, turns={len(self.turns)}, has_summary={bool(self.summary)})"


# Convenience function for creating new session
def create_session(session_id: Optional[str] = None) -> SessionMemory:
    """
    Create a new session memory.
    
    Args:
        session_id: Optional custom session ID
        
    Returns:
        New SessionMemory instance
    """
    if session_id:
        return SessionMemory(session_id=session_id)
    return SessionMemory()


# Convenience function for loading or creating session
def get_or_create_session(
    session_id: Optional[str] = None,
    directory: str = SESSION_DIR
) -> SessionMemory:
    """
    Load existing session or create new one.
    
    Args:
        session_id: Session ID to load (None = create new)
        directory: Directory for session files
        
    Returns:
        SessionMemory instance
    """
    if session_id:
        existing = SessionMemory.load_from_disk(session_id, directory)
        if existing:
            return existing
    
    return create_session(session_id)

