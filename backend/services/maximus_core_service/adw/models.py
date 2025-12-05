"""
ADW Request/Response Models.

Pydantic models for AI-Driven Workflows API.

Author: MAXIMUS Team
Date: 2025-10-15
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class CampaignRequest(BaseModel):
    """Request model for creating offensive campaign."""

    objective: str
    scope: list[str]
    constraints: dict[str, Any] | None = None


class CampaignResponse(BaseModel):
    """Response model for campaign creation."""

    campaign_id: str
    status: str
    created_at: str


class AttackSurfaceRequest(BaseModel):
    """Request model for attack surface mapping workflow."""

    domain: str
    include_subdomains: bool = True
    port_range: str | None = None
    scan_depth: str = "standard"


class CredentialIntelRequest(BaseModel):
    """Request model for credential intelligence workflow."""

    email: str | None = None
    username: str | None = None
    phone: str | None = None
    include_darkweb: bool = True
    include_dorking: bool = True
    include_social: bool = True


class ProfileTargetRequest(BaseModel):
    """Request model for target profiling workflow."""

    username: str | None = None
    email: str | None = None
    phone: str | None = None
    name: str | None = None
    location: str | None = None
    image_url: str | None = None
    include_social: bool = True
    include_images: bool = True
