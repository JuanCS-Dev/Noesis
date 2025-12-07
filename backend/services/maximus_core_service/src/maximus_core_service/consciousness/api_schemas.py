"""
Consciousness API Schemas - Pydantic models for API request/response.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SalienceInput(BaseModel):
    """Salience score for manual ESGT trigger."""

    novelty: float = Field(..., ge=0.0, le=1.0, description="Novelty component [0-1]")
    relevance: float = Field(..., ge=0.0, le=1.0, description="Relevance component [0-1]")
    urgency: float = Field(..., ge=0.0, le=1.0, description="Urgency component [0-1]")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context")


class ArousalAdjustment(BaseModel):
    """Arousal level adjustment request."""

    delta: float = Field(..., ge=-0.5, le=0.5, description="Arousal change [-0.5, +0.5]")
    duration_seconds: float = Field(default=5.0, ge=0.1, le=60.0, description="Duration")
    source: str = Field(default="manual", description="Source identifier")


class ConsciousnessStateResponse(BaseModel):
    """Complete consciousness state snapshot."""

    timestamp: str
    esgt_active: bool
    arousal_level: float
    arousal_classification: str
    tig_metrics: dict[str, Any]
    recent_events_count: int
    system_health: str


class ESGTEventResponse(BaseModel):
    """ESGT ignition event."""

    event_id: str
    timestamp: str
    success: bool
    salience: dict[str, float]
    coherence: float | None
    duration_ms: float | None
    nodes_participating: int
    reason: str | None


class SafetyStatusResponse(BaseModel):
    """Safety protocol status (FASE VII)."""

    monitoring_active: bool
    kill_switch_active: bool
    violations_total: int
    violations_by_severity: dict[str, int]
    last_violation: str | None
    uptime_seconds: float


class SafetyViolationResponse(BaseModel):
    """Safety violation event (FASE VII)."""

    violation_id: str
    violation_type: str
    severity: str
    timestamp: str
    value_observed: float
    threshold_violated: float
    message: str
    context: dict[str, Any]


class EmergencyShutdownRequest(BaseModel):
    """Emergency shutdown request (HITL only - FASE VII)."""

    reason: str = Field(..., min_length=10, description="Human-readable reason (min 10 chars)")
    allow_override: bool = Field(default=True, description="Allow HITL override (5s window)")
