"""
AI-Driven Workflows (ADW) Package.

Provides unified API endpoints for Offensive AI (Red Team),
Defensive AI (Blue Team), and Purple Team co-evolution workflows.

Author: MAXIMUS Team
Date: 2025-10-15
"""

from __future__ import annotations

from .models import (
    AttackSurfaceRequest,
    CampaignRequest,
    CampaignResponse,
    CredentialIntelRequest,
    ProfileTargetRequest,
)
from .router import router

__all__ = [
    # Main router
    "router",
    # Request/Response models
    "AttackSurfaceRequest",
    "CampaignRequest",
    "CampaignResponse",
    "CredentialIntelRequest",
    "ProfileTargetRequest",
]
