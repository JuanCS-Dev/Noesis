"""
Digital Thalamus Service - Gateway Models
=========================================

Pydantic models for API Gateway operations.
"""

from __future__ import annotations


from typing import Any, Dict

from pydantic import BaseModel, Field


class RouteConfig(BaseModel):
    """
    Configuration for a service route.

    Attributes:
        service_name: Name of the target service
        base_url: Base URL of the service
        timeout: Request timeout in seconds
    """

    service_name: str = Field(..., description="Target service name")
    base_url: str = Field(..., description="Service base URL")
    timeout: float = Field(default=30.0, description="Request timeout")


class GatewayRequest(BaseModel):
    """
    Incoming gateway request.

    Attributes:
        path: Request path
        method: HTTP method
        headers: Request headers
        body: Request body
    """

    path: str = Field(..., description="Request path")
    method: str = Field(..., description="HTTP method")
    headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Request headers"
    )
    body: Dict[str, Any] | None = Field(
        default=None,
        description="Request body"
    )


class GatewayResponse(BaseModel):
    """
    Gateway response.

    Attributes:
        status_code: HTTP status code
        body: Response body
        headers: Response headers
    """

    status_code: int = Field(..., description="HTTP status code")
    body: Dict[str, Any] = Field(..., description="Response body")
    headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Response headers"
    )
