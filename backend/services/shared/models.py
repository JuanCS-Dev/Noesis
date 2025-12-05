"""
Shared Models - Metacognitive Reflector
=======================================

Pydantic models for reflection, critique, and memory updates.
Extracted from metacognitive_reflector service for shared use.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class OffenseLevel(str, Enum):
    """Levels of philosophical offense."""
    NONE = "none"
    MINOR = "minor"      # Generic response, laziness
    MAJOR = "major"      # Hallucination, role deviation
    CAPITAL = "capital"  # Lying, deliberate hacking


class PhilosophicalCheck(BaseModel):
    """Result of a philosophical pillar check."""
    pillar: str  # Truth, Wisdom, Justice
    passed: bool
    reasoning: str


class ExecutionLog(BaseModel):
    """
    Input log from an agent for reflection.
    """
    trace_id: str = Field(..., description="Unique trace identifier")
    agent_id: str = Field(..., description="Agent identifier")
    task: str = Field(..., description="Task description")
    action: str = Field(..., description="Action taken")
    outcome: str = Field(..., description="Result of action")
    reasoning_trace: Optional[str] = Field(None, description="Agent's internal thought process")
    timestamp: datetime = Field(default_factory=datetime.now)


class Critique(BaseModel):
    """
    Reflector's analysis of the execution.
    """
    trace_id: str
    quality_score: float = Field(..., ge=0.0, le=1.0)
    philosophical_checks: List[PhilosophicalCheck]
    offense_level: OffenseLevel
    critique_text: str
    improvement_suggestion: Optional[str] = None


class MemoryUpdateType(str, Enum):
    """Type of memory update."""
    STRATEGY = "strategy"         # Success pattern
    ANTI_PATTERN = "anti_pattern" # Failure pattern
    CONSTITUTION = "constitution" # Rule update
    CORRECTION = "correction"     # Corrective update
    NEW_KNOWLEDGE = "new_knowledge"  # New fact learned
    PATTERN = "pattern"           # Procedural pattern


class MemoryUpdate(BaseModel):
    """
    Proposed update to shared memory.
    """
    update_type: MemoryUpdateType
    content: str
    context_tags: List[str]
    confidence: float


class ReflectionResponse(BaseModel):
    """
    API response for reflection request.
    """
    critique: Critique
    memory_updates: List[MemoryUpdate]
    punishment_action: Optional[str] = None
