"""
HCL Planner Service - API Request Models
========================================

Pydantic models for API request validation.
"""

from __future__ import annotations

from typing import Dict, Any
from pydantic import BaseModel, Field


class PlanRequest(BaseModel):
    """
    Request model for plan generation endpoint.

    Attributes:
        current_state: Current system metrics
        analysis_result: Analysis insights from HCL Analyzer
        operational_goals: Desired operational outcomes
    """

    current_metrics: Dict[str, float] = Field(
        ..., description="Current system resource metrics"
    )
    analysis_result: Dict[str, Any] = Field(
        ..., description="Analysis insights from HCL Analyzer"
    )
    operational_goals: Dict[str, Any] = Field(
        ..., description="Desired operational outcomes"
    )

    class Config:  # pylint: disable=too-few-public-methods,missing-class-docstring
        schema_extra = {
            "example": {
                "current_state": {
                    "cpu_usage": 0.85,
                    "memory_usage": 0.60,
                    "pod_count": 3
                },
                "analysis_result": {
                    "bottleneck": "cpu",
                    "trend": "increasing",
                    "severity": "high"
                },
                "operational_goals": {
                    "target_cpu": 0.70,
                    "max_replicas": 10,
                    "min_replicas": 2
                }
            }
        }
