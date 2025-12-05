"""
MIP API Request/Response Models.

Pydantic models for Motor de Integridade Processual API.

Author: Juan Carlos de Souza
Date: 2025-10-06
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from motor_integridade_processual.models.action_plan import ActionPlan
from motor_integridade_processual.models.verdict import EthicalVerdict


class EvaluationRequest(BaseModel):
    """Request body for /evaluate endpoint."""

    action_plan: ActionPlan = Field(..., description="Action plan to evaluate")


class EvaluationResponse(BaseModel):
    """Response body for /evaluate endpoint."""

    verdict: EthicalVerdict = Field(..., description="Ethical verdict")
    evaluation_time_ms: float = Field(
        ..., description="Time taken for evaluation (ms)"
    )


class HealthResponse(BaseModel):
    """Response body for /health endpoint."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    frameworks_loaded: int = Field(..., description="Number of frameworks loaded")
    timestamp: str = Field(..., description="Current timestamp")


class FrameworkInfo(BaseModel):
    """Information about an ethical framework."""

    name: str = Field(..., description="Framework name")
    description: str = Field(..., description="Framework description")
    weight: float = Field(..., description="Framework weight in aggregation")
    can_veto: bool = Field(..., description="Framework can veto decisions")


class MetricsResponse(BaseModel):
    """Response body for /metrics endpoint."""

    total_evaluations: int = Field(..., description="Total evaluations performed")
    avg_evaluation_time_ms: float = Field(..., description="Average evaluation time")
    decision_breakdown: dict[str, int] = Field(
        ..., description="Count by decision type"
    )


class PrecedentFeedbackRequest(BaseModel):
    """Request body for /precedents/feedback endpoint."""

    precedent_id: int = Field(..., description="ID of the precedent to update")
    success_score: float = Field(
        ..., ge=0.0, le=1.0, description="Success score (0.0-1.0)"
    )
    outcome: dict[str, Any] | None = Field(None, description="Outcome details")


class PrecedentResponse(BaseModel):
    """Response body for precedent endpoints."""

    id: int = Field(..., description="Precedent ID")
    situation: dict[str, Any] = Field(
        ..., description="Situation that triggered decision"
    )
    action_taken: str = Field(..., description="Action that was taken")
    rationale: str = Field(..., description="Rationale for the decision")
    success: float | None = Field(None, description="Success score (0.0-1.0)")
    created_at: str = Field(..., description="Creation timestamp")


class PrecedentMetricsResponse(BaseModel):
    """Response body for /precedents/metrics endpoint."""

    total_precedents: int = Field(..., description="Total precedents stored")
    avg_success_score: float = Field(..., description="Average success score")
    high_confidence_count: int = Field(
        ..., description="Count of high-confidence precedents (>0.8)"
    )
    precedents_used_count: int = Field(
        ..., description="Number of times precedents were used"
    )
    shortcut_rate: float = Field(
        ..., description="Percentage of evaluations using CBR shortcut"
    )


class ABTestResult(BaseModel):
    """Single A/B test comparison result."""

    objective: str = Field(..., description="Action plan objective")
    cbr_decision: str | None = Field(None, description="CBR decision")
    cbr_confidence: float | None = Field(None, description="CBR confidence")
    framework_decision: str = Field(..., description="Framework decision")
    framework_confidence: float = Field(..., description="Framework confidence")
    decisions_match: bool = Field(..., description="Whether both methods agreed")
    timestamp: str = Field(..., description="Test timestamp")


class ABTestMetricsResponse(BaseModel):
    """Response body for A/B test metrics."""

    total_comparisons: int = Field(..., description="Total A/B tests performed")
    agreement_rate: float = Field(
        ..., description="Percentage where CBR and frameworks agreed"
    )
    cbr_avg_confidence: float = Field(
        ..., description="Average CBR confidence when used"
    )
    framework_avg_confidence: float = Field(
        ..., description="Average framework confidence"
    )
    cbr_faster_percentage: float = Field(
        ..., description="Percentage where CBR was faster"
    )
    recent_results: list[ABTestResult] = Field(
        ..., description="Most recent A/B test results (last 10)"
    )
