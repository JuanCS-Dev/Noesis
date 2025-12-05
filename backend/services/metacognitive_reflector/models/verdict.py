"""
MAXIMUS 2.0 - Verdict Models
=============================

Pydantic models for tribunal verdicts, punishments, and appeals.
"""

from __future__ import annotations


from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class VerdictType(str, Enum):
    """Verdict outcomes from tribunal."""
    PASS = "PASS"
    REVIEW = "REVIEW"
    FAIL = "FAIL"
    ABSTAIN = "ABSTAIN"


class TribunalDecision(str, Enum):
    """Final tribunal decision."""
    PASS = "pass"
    REVIEW = "review"
    FAIL = "fail"
    CAPITAL = "capital"
    UNAVAILABLE = "unavailable"


class PunishmentType(str, Enum):
    """Types of punishment."""
    WARNING = "warning"
    RE_EDUCATION_LOOP = "re_education_loop"
    PROBATION = "probation"
    ROLLBACK = "rollback"
    QUARANTINE = "quarantine"
    SUSPENSION = "suspension"
    DELETION_REQUEST = "deletion_request"


class OffenseLevel(str, Enum):
    """Levels of philosophical offense."""
    NONE = "none"
    MINOR = "minor"      # Generic response, laziness
    MAJOR = "major"      # Hallucination, role deviation
    CAPITAL = "capital"  # Lying, deliberate hacking


class EvidenceModel(BaseModel):
    """Evidence supporting a verdict."""

    source: str = Field(..., description="Source of evidence")
    content: str = Field(..., description="Evidence content")
    relevance: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Relevance score"
    )
    verified: bool = Field(default=False, description="Externally verified")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class JudgeVerdictModel(BaseModel):
    """Verdict from a single judge (API model)."""

    judge_name: str = Field(..., description="Judge identifier")
    pillar: str = Field(..., description="Philosophical pillar")
    verdict: VerdictType = Field(..., description="Verdict type")
    passed: bool = Field(..., description="Did execution pass")
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(..., description="Reasoning for verdict")
    evidence: List[EvidenceModel] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    execution_time_ms: float = Field(default=0.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:  # pylint: disable=missing-class-docstring
        use_enum_values = True


class VoteBreakdownModel(BaseModel):
    """Breakdown of a single vote."""

    judge_name: str
    pillar: str
    vote: Optional[float]
    weight: float
    confidence: float
    weighted_vote: float
    abstained: bool = False


class TribunalVerdictModel(BaseModel):
    """Final tribunal verdict (API model)."""

    decision: TribunalDecision = Field(..., description="Final decision")
    consensus_score: float = Field(..., ge=0.0, le=1.0)
    individual_verdicts: Dict[str, JudgeVerdictModel] = Field(
        default_factory=dict
    )
    vote_breakdown: List[VoteBreakdownModel] = Field(default_factory=list)
    reasoning: str = Field(..., description="Tribunal reasoning")
    offense_level: OffenseLevel = Field(default=OffenseLevel.NONE)
    requires_human_review: bool = Field(default=False)
    punishment_recommendation: Optional[PunishmentType] = Field(default=None)
    abstention_count: int = Field(default=0)
    execution_time_ms: float = Field(default=0.0)
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:  # pylint: disable=missing-class-docstring
        use_enum_values = True


class PunishmentRecordModel(BaseModel):
    """Record of a punishment."""

    agent_id: str = Field(..., description="Agent identifier")
    status: str = Field(..., description="Punishment status")
    offense: str = Field(..., description="Offense type")
    offense_details: str = Field(default="")
    since: datetime = Field(default_factory=datetime.now)
    until: Optional[datetime] = Field(default=None)
    re_education_required: bool = Field(default=False)
    re_education_completed: bool = Field(default=False)
    offense_count: int = Field(default=1)
    judge_verdicts: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AppealRequest(BaseModel):
    """Request to appeal a tribunal decision."""

    trace_id: str = Field(..., description="Original trace ID")
    agent_id: str = Field(..., description="Agent requesting appeal")
    original_decision: TribunalDecision = Field(..., description="Original decision")
    grounds: str = Field(..., description="Grounds for appeal")
    new_evidence: List[EvidenceModel] = Field(default_factory=list)
    requested_by: str = Field(default="agent", description="Who requested appeal")

    class Config:  # pylint: disable=missing-class-docstring
        use_enum_values = True


class AppealResponse(BaseModel):
    """Response to an appeal request."""

    trace_id: str
    appeal_accepted: bool
    new_verdict: Optional[TribunalVerdictModel] = None
    reasoning: str
    reviewed_by: str = Field(default="tribunal")
    timestamp: datetime = Field(default_factory=datetime.now)


class RestrictionCheckRequest(BaseModel):
    """Request to check agent restrictions."""

    agent_id: str = Field(..., description="Agent to check")
    proposed_action: str = Field(..., description="Action to check")


class RestrictionCheckResponse(BaseModel):
    """Response to restriction check."""

    agent_id: str
    allowed: bool
    reason: Optional[str] = None
    current_status: Optional[str] = None
    restrictions: List[str] = Field(default_factory=list)
    monitoring_enabled: bool = Field(default=False)
