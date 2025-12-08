"""
NOESIS Memory Fortress - Soul Evolution Tracker (Simplified)
=============================================================

Simplified tracker for soul evolution in the metacognitive_reflector service.
Full implementation in maximus_core_service/consciousness/exocortex/soul.

This version:
- Stores events via MemoryClient (Memory Fortress)
- Persists to JSON backup
- No dependency on maximus_core_service

Based on:
- Memory Fortress Architecture
- Soul Evolution patterns from maximus_core_service
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from .memory import MemoryClient, MemoryType

logger = logging.getLogger(__name__)


class SoulEventType(str, Enum):
    """Types of soul evolution events."""
    LEARNING = "learning"
    VALUE_UPHELD = "value_upheld"
    VALUE_TESTED = "value_tested"
    VALUE_CHALLENGED = "value_challenged"
    REFLECTION = "reflection"
    CONSCIENCE_OBJECTION = "conscience"
    GROWTH = "growth"


class SoulPillar(str, Enum):
    """The three pillars."""
    VERITAS = "VERITAS"
    SOPHIA = "SOPHIA"
    DIKE = "DIKĒ"


class SoulTracker:
    """
    Simplified soul evolution tracker for metacognitive_reflector.
    
    Records:
    - Learning events (patterns validated)
    - Value events (upheld/tested/challenged)
    - Conscience objections (AIITL)
    
    Storage:
    - Memory Fortress via MemoryClient
    - JSON backup with checksums
    """
    
    def __init__(
        self,
        memory_client: Optional[MemoryClient] = None,
        backup_path: str = "data/soul_tracker.json",
    ) -> None:
        """
        Initialize tracker.
        
        Args:
            memory_client: MemoryClient for persistence
            backup_path: Path for JSON backup
        """
        self._memory = memory_client
        self._backup_path = Path(backup_path)
        self._backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory event log
        self._events: List[Dict[str, Any]] = []
        
        # Counters
        self._learning_count = 0
        self._value_upheld = 0
        self._value_challenged = 0
        self._conscience_count = 0
        
        # Load existing
        self._load_backup()
    
    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique = uuid.uuid4().hex[:6]
        return f"{prefix}_{timestamp}_{unique}"
    
    async def record_learning(
        self,
        context: str,
        insight: str,
        source: str = "tribunal",
        pillar: Optional[str] = None,
        importance: float = 0.7,
    ) -> str:
        """
        Record a learning event.
        
        Args:
            context: What happened
            insight: What was learned
            source: Source of learning
            pillar: Related pillar
            importance: Importance (0-1)
            
        Returns:
            Event ID
        """
        event = {
            "event_id": self._generate_id("learn"),
            "event_type": SoulEventType.LEARNING.value,
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "insight": insight,
            "source": source,
            "pillar": pillar,
            "importance": importance,
        }
        
        await self._persist_event(event)
        self._learning_count += 1
        
        logger.debug(f"Learning recorded: {insight[:50]}...")
        return event["event_id"]
    
    async def record_value_event(
        self,
        value_rank: int,
        event_type: Literal["upheld", "tested", "challenged"],
        context: str,
        value_name: str = "",
    ) -> str:
        """
        Record a value event.
        
        Args:
            value_rank: Rank of value (1-5)
            event_type: upheld/tested/challenged
            context: What happened
            value_name: Name of the value
            
        Returns:
            Event ID
        """
        # Importance based on rank
        importance = 1.0 - (value_rank - 1) * 0.15
        
        event_type_map = {
            "upheld": SoulEventType.VALUE_UPHELD,
            "tested": SoulEventType.VALUE_TESTED,
            "challenged": SoulEventType.VALUE_CHALLENGED,
        }
        
        event = {
            "event_id": self._generate_id("value"),
            "event_type": event_type_map.get(event_type, SoulEventType.VALUE_TESTED).value,
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "value_rank": value_rank,
            "value_name": value_name or f"Rank {value_rank}",
            "outcome": event_type,
            "importance": importance,
        }
        
        await self._persist_event(event)
        
        if event_type == "upheld":
            self._value_upheld += 1
        elif event_type == "challenged":
            self._value_challenged += 1
        
        logger.debug(f"Value event: {value_name or value_rank} {event_type}")
        return event["event_id"]
    
    async def record_conscience_objection(
        self,
        context: str,
        reason: str,
        directive: str,
    ) -> str:
        """
        Record an AIITL conscience objection.
        
        Args:
            context: Context of objection
            reason: Why objecting
            directive: Which directive was applied
            
        Returns:
            Event ID
        """
        event = {
            "event_id": self._generate_id("conscience"),
            "event_type": SoulEventType.CONSCIENCE_OBJECTION.value,
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "reason": reason,
            "directive": directive,
            "importance": 0.9,
            "pillar": SoulPillar.DIKE.value,
        }
        
        await self._persist_event(event)
        self._conscience_count += 1
        
        logger.info(f"Conscience objection recorded: {reason[:50]}...")
        return event["event_id"]
    
    async def record_reflection(
        self,
        context: str,
        insight: str,
        pillar: Optional[str] = None,
    ) -> str:
        """
        Record a metacognitive reflection.
        
        Args:
            context: Context of reflection
            insight: The reflection
            pillar: Related pillar
            
        Returns:
            Event ID
        """
        event = {
            "event_id": self._generate_id("reflect"),
            "event_type": SoulEventType.REFLECTION.value,
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "insight": insight,
            "pillar": pillar,
            "importance": 0.6,
        }
        
        await self._persist_event(event)
        
        logger.debug(f"Reflection recorded: {insight[:50]}...")
        return event["event_id"]
    
    async def _persist_event(self, event: Dict[str, Any]) -> None:
        """Persist event to all tiers."""
        # Add to memory
        self._events.append(event)
        
        # Persist to MemoryClient
        if self._memory:
            try:
                content = f"[SOUL:{event['event_type'].upper()}] {event.get('insight', event.get('context', ''))}"
                await self._memory.store(
                    content=content,
                    memory_type=MemoryType.REFLECTION,
                    importance=event.get("importance", 0.5),
                    context={
                        "soul_event": True,
                        "event_type": event["event_type"],
                        "pillar": event.get("pillar"),
                        "event_id": event["event_id"],
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to persist soul event to Memory Fortress: {e}")
        
        # Save to JSON backup
        self._save_backup()
    
    def _load_backup(self) -> None:
        """Load from JSON backup."""
        if not self._backup_path.exists():
            return
        
        try:
            with open(self._backup_path, "r") as f:
                data = json.load(f)
            
            # Verify checksum
            stored_checksum = data.get("_checksum")
            if stored_checksum:
                content = {k: v for k, v in data.items() if k != "_checksum"}
                calculated = self._calculate_checksum(content)
                if calculated != stored_checksum:
                    logger.error("Soul tracker backup checksum mismatch!")
                    return
            
            self._events = data.get("events", [])
            self._learning_count = data.get("counters", {}).get("learning", 0)
            self._value_upheld = data.get("counters", {}).get("value_upheld", 0)
            self._value_challenged = data.get("counters", {}).get("value_challenged", 0)
            self._conscience_count = data.get("counters", {}).get("conscience", 0)
            
            logger.info(f"Loaded {len(self._events)} soul events from backup")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load soul tracker backup: {e}")
    
    def _save_backup(self) -> None:
        """Save to JSON backup with checksum."""
        content = {
            "events": self._events,
            "counters": {
                "learning": self._learning_count,
                "value_upheld": self._value_upheld,
                "value_challenged": self._value_challenged,
                "conscience": self._conscience_count,
            },
            "_updated_at": datetime.now().isoformat(),
        }
        
        data = {
            **content,
            "_checksum": self._calculate_checksum(content),
        }
        
        # Atomic write
        temp_path = self._backup_path.with_suffix(".json.tmp")
        with open(temp_path, "w") as f:
            json.dump(data, f, indent=2)
        temp_path.rename(self._backup_path)
    
    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate SHA-256 checksum."""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def get_value_integrity_score(self) -> float:
        """Get value integrity score."""
        total = self._value_upheld + self._value_challenged
        if total == 0:
            return 1.0
        return self._value_upheld / total
    
    def get_summary(self) -> Dict[str, Any]:
        """Get evolution summary."""
        return {
            "total_events": len(self._events),
            "learning_count": self._learning_count,
            "value_upheld": self._value_upheld,
            "value_challenged": self._value_challenged,
            "conscience_objections": self._conscience_count,
            "value_integrity": self.get_value_integrity_score(),
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check tracker health."""
        return {
            "healthy": True,
            "events_stored": len(self._events),
            "memory_client_available": self._memory is not None,
            "backup_path": str(self._backup_path),
            **self.get_summary(),
        }

