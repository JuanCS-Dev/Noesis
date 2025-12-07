"""
Maximus Core Service - System Models
====================================

Pydantic models for system state and health.
"""

from __future__ import annotations


from datetime import datetime
from typing import Dict

from pydantic import BaseModel, Field


class ServiceHealth(BaseModel):
    """
    Health status of a single service.

    Attributes:
        service_name: Name of the service
        status: Health status (healthy, degraded, unhealthy)
        timestamp: When health was checked
        details: Additional details about health status
    """

    service_name: str = Field(..., description="Service name")
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    details: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional status details"
    )


class SystemStatus(BaseModel):
    """
    Overall system health status.

    Attributes:
        status: Overall system status
        timestamp: Status check timestamp
        services: Health status of all services
        total_services: Total number of services
        healthy_services: Number of healthy services
    """

    status: str = Field(..., description="Overall system status")
    timestamp: datetime = Field(..., description="Status timestamp")
    services: Dict[str, ServiceHealth] = Field(
        default_factory=dict,
        description="Service health statuses"
    )
    total_services: int = Field(..., description="Total services count")
    healthy_services: int = Field(..., description="Healthy services count")
