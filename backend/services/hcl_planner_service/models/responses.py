"""
HCL Planner Service - API Response Models
=========================================

Pydantic models for API responses.
"""

from __future__ import annotations

from typing import Dict, Any, List
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """
    Response model for health check endpoint.

    Attributes:
        status: Overall service status
        service: Service identifier
        planner: Planner-specific health info
    """

    status: str = Field(..., description="Overall service status")
    service: str = Field(..., description="Service identifier")
    planner: Dict[str, Any] = Field(..., description="Planner health details")


class PlanResponse(BaseModel):
    """
    Response model for plan generation endpoint.

    Attributes:
        plan_id: Unique plan identifier
        timestamp: Plan generation timestamp
        actions: Recommended actions
    """

    plan_id: str = Field(..., description="Unique plan identifier")
    timestamp: float = Field(..., description="Unix timestamp")
    actions: List[Dict[str, Any]] = Field(
        ...,
        description="Recommended infrastructure actions"
    )

    class Config:  # pylint: disable=too-few-public-methods,missing-class-docstring
        schema_extra = {
            "example": {
                "plan_id": "plan-a1b2c3d4",
                "timestamp": 1701368400.0,
                "actions": [
                    {
                        "type": "scale_deployment",
                        "parameters": {
                            "deployment_name": "api-server",
                            "namespace": "production",
                            "replicas": 5
                        }
                    }
                ]
            }
        }


class MessageResponse(BaseModel):
    """
    Generic message response.

    Attributes:
        message: Response message
    """

    message: str = Field(..., description="Response message")
