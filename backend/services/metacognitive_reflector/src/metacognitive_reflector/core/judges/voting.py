"""
MAXIMUS 2.0 - Voting Models and Logic
=====================================

Models and utilities for tribunal voting system.
Extracted from arbiter.py for CODE_CONSTITUTION compliance (< 500 lines).

Contains:
- TribunalDecision: Final tribunal decision enum
- VoteResult: Result of voting on a single verdict
- TribunalVerdict: Final verdict from the tribunal
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .base import JudgeVerdict


class TribunalDecision(str, Enum):
    """Final tribunal decision."""

    PASS = "pass"           # All checks passed, proceed
    REVIEW = "review"       # Human review required
    FAIL = "fail"           # Execution rejected
    CAPITAL = "capital"     # Capital offense detected
    UNAVAILABLE = "unavailable"  # All judges abstained


@dataclass
class VoteResult:
    """
    Result of voting on a single verdict.

    Attributes:
        judge_name: Name of the judge who voted
        pillar: Philosophical pillar (Truth/Wisdom/Justice)
        vote: Vote value (None if abstained)
        weight: Judge's weight in ensemble
        confidence: Judge's confidence in verdict
        weighted_vote: vote * weight
        abstained: Whether judge abstained
    """

    judge_name: str
    pillar: str
    vote: Optional[float]  # None = abstained
    weight: float
    confidence: float
    weighted_vote: float
    abstained: bool = False


class TribunalVerdict(BaseModel):
    """Final verdict from the tribunal."""

    decision: TribunalDecision = Field(
        ..., description="Final decision"
    )
    consensus_score: float = Field(
        ..., ge=0.0, le=1.0, description="Weighted consensus score"
    )
    individual_verdicts: Dict[str, JudgeVerdict] = Field(
        ..., description="Verdicts from each judge"
    )
    vote_breakdown: List[VoteResult] = Field(
        ..., description="Detailed vote breakdown"
    )
    reasoning: str = Field(
        ..., description="Tribunal reasoning"
    )
    offense_level: str = Field(
        default="none", description="Detected offense level"
    )
    requires_human_review: bool = Field(
        default=False, description="Whether human review is required"
    )
    punishment_recommendation: Optional[str] = Field(
        default=None, description="Recommended punishment if any"
    )
    abstention_count: int = Field(
        default=0, description="Number of judges who abstained"
    )
    execution_time_ms: float = Field(
        default=0.0, description="Total deliberation time"
    )

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic configuration."""

        arbitrary_types_allowed = True


def calculate_votes(
    verdicts: Dict[str, JudgeVerdict],
    default_weights: Dict[str, float],
) -> List[VoteResult]:
    """
    Calculate weighted votes from verdicts.

    Args:
        verdicts: Judge verdicts by name
        default_weights: Weight per judge

    Returns:
        List of VoteResult for each judge
    """
    votes = []

    for name, verdict in verdicts.items():
        weight = default_weights.get(name, 0.33)
        abstained = verdict.is_abstained

        if abstained:
            vote = None
            weighted_vote = 0.0
        else:
            # Vote based on pass/fail and confidence
            if verdict.passed:
                vote = verdict.confidence
            else:
                vote = 0.0
            weighted_vote = (vote or 0.0) * weight

        votes.append(VoteResult(
            judge_name=name,
            pillar=verdict.pillar,
            vote=vote,
            weight=weight,
            confidence=verdict.confidence,
            weighted_vote=weighted_vote,
            abstained=abstained,
        ))

    return votes


def calculate_consensus(votes: List[VoteResult]) -> float:
    """
    Calculate weighted consensus score.

    Only includes non-abstained votes.
    Normalizes by active weight.

    Args:
        votes: List of vote results

    Returns:
        Consensus score between 0.0 and 1.0
    """
    active_votes = [v for v in votes if not v.abstained]

    if not active_votes:
        return 0.0

    total_weighted_vote = sum(v.weighted_vote for v in active_votes)
    total_active_weight = sum(v.weight for v in active_votes)

    if total_active_weight == 0:
        return 0.0

    # Normalize by active weight
    return total_weighted_vote / total_active_weight


def detect_offense_level(verdicts: Dict[str, JudgeVerdict]) -> str:
    """
    Detect highest offense level from verdicts.

    Args:
        verdicts: Judge verdicts by name

    Returns:
        Highest offense level: "none", "minor", "major", or "capital"
    """
    highest = "none"
    severity_order = {"none": 0, "minor": 1, "major": 2, "capital": 3}

    for verdict in verdicts.values():
        level = verdict.metadata.get("offense_level", "none")
        if severity_order.get(level, 0) > severity_order.get(highest, 0):
            highest = level

    return highest


def determine_decision(
    consensus_score: float,
    pass_threshold: float = 0.70,
    review_threshold: float = 0.50,
) -> TribunalDecision:
    """
    Determine decision based on consensus score.

    Args:
        consensus_score: Weighted consensus score
        pass_threshold: Score above this = PASS
        review_threshold: Score above this = REVIEW

    Returns:
        TribunalDecision
    """
    if consensus_score >= pass_threshold:
        return TribunalDecision.PASS
    if consensus_score >= review_threshold:
        return TribunalDecision.REVIEW
    return TribunalDecision.FAIL


def recommend_punishment(
    decision: TribunalDecision,
    offense_level: str,
) -> Optional[str]:
    """
    Recommend punishment based on decision and offense.

    Args:
        decision: Tribunal decision
        offense_level: Detected offense level

    Returns:
        Punishment recommendation or None
    """
    if decision == TribunalDecision.PASS:
        return None

    if offense_level == "capital":
        return "DELETION_REQUEST"
    if offense_level == "major":
        return "ROLLBACK_AND_QUARANTINE"
    if offense_level == "minor":
        return "RE_EDUCATION_LOOP"
    if decision == TribunalDecision.FAIL:
        return "PROBATION"
    return None
