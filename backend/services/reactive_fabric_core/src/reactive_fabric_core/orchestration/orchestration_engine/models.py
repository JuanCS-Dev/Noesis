"""
Models for Orchestration Engine.

Enums and Pydantic models for event correlation and threat analysis.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field


class EventCorrelationWindow(Enum):
    """Time windows for event correlation."""

    IMMEDIATE = 1   # 1 minute
    SHORT = 5       # 5 minutes
    MEDIUM = 15     # 15 minutes
    LONG = 60       # 60 minutes


class ThreatCategory(Enum):
    """Categories of threats."""

    RECONNAISSANCE = "reconnaissance"
    INITIAL_ACCESS = "initial_access"
    EXECUTION = "execution"
    PERSISTENCE = "persistence"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DEFENSE_EVASION = "defense_evasion"
    CREDENTIAL_ACCESS = "credential_access"
    DISCOVERY = "discovery"
    LATERAL_MOVEMENT = "lateral_movement"
    COLLECTION = "collection"
    EXFILTRATION = "exfiltration"
    IMPACT = "impact"


class OrchestrationConfig(BaseModel):
    """Configuration for Orchestration Engine."""

    correlation_window_minutes: int = Field(
        default=15, description="Time window for correlating events"
    )
    max_events_per_window: int = Field(
        default=10000, description="Max events to keep in correlation window"
    )
    base_score_threshold: float = Field(
        default=0.3, description="Minimum score to consider as threat"
    )
    critical_score_threshold: float = Field(
        default=0.8, description="Score threshold for critical threats"
    )
    min_events_for_pattern: int = Field(
        default=3, description="Minimum events to detect a pattern"
    )
    anomaly_sensitivity: float = Field(
        default=0.7, description="Sensitivity for anomaly detection (0-1)"
    )
    max_correlation_rules: int = Field(
        default=100, description="Maximum active correlation rules"
    )
    event_ttl_minutes: int = Field(
        default=60, description="Time to keep events in memory"
    )


class CorrelationRule(BaseModel):
    """Defines a correlation rule for event patterns."""

    rule_id: str
    name: str
    description: str
    category: ThreatCategory
    event_types: List[str]
    time_window: EventCorrelationWindow
    min_occurrences: int
    base_score: float
    score_multiplier: float = Field(default=1.0)
    mitre_tactics: List[str] = Field(default_factory=list)
    mitre_techniques: List[str] = Field(default_factory=list)


class ThreatScore(BaseModel):
    """Calculated threat score for correlated events."""

    score_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    base_score: float
    confidence: float
    severity: str
    category: ThreatCategory
    correlated_events: List[str]
    matched_rules: List[str]
    source_ips: Set[str] = Field(default_factory=set)
    target_systems: Set[str] = Field(default_factory=set)
    attack_timeline: List[Tuple[datetime, str]] = Field(default_factory=list)
    mitre_tactics: Set[str] = Field(default_factory=set)
    mitre_techniques: Set[str] = Field(default_factory=set)


class OrchestrationEvent(BaseModel):
    """Enhanced event with orchestration metadata."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    collector_type: str
    source: str
    severity: str
    raw_data: Dict[str, Any]
    correlation_id: Optional[str] = None
    threat_score: Optional[float] = None
    matched_patterns: List[str] = Field(default_factory=list)
    related_events: List[str] = Field(default_factory=list)
    tags: Set[str] = Field(default_factory=set)
