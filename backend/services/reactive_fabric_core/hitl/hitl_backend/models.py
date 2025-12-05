"""HITL Backend - Models and Enums.

Pydantic models and enumerations for the HITL decision system.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """User roles for RBAC."""

    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class DecisionStatus(str, Enum):
    """Decision workflow status."""

    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class DecisionPriority(str, Enum):
    """Decision priority levels."""

    CRITICAL = "critical"  # APT, nation-state
    HIGH = "high"  # Targeted attacks
    MEDIUM = "medium"  # Opportunistic
    LOW = "low"  # Noise


class ActionType(str, Enum):
    """Available response actions."""

    BLOCK_IP = "block_ip"
    QUARANTINE_SYSTEM = "quarantine_system"
    ACTIVATE_KILLSWITCH = "activate_killswitch"
    DEPLOY_COUNTERMEASURE = "deploy_countermeasure"
    ESCALATE_TO_SOC = "escalate_to_soc"
    NO_ACTION = "no_action"
    CUSTOM = "custom"


class UserCreate(BaseModel):
    """User registration model."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    role: UserRole = UserRole.ANALYST


class UserInDB(BaseModel):
    """User database model."""

    username: str
    email: str
    full_name: str
    role: UserRole
    hashed_password: str
    is_active: bool = True
    is_2fa_enabled: bool = False
    totp_secret: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    requires_2fa: bool = False


class TokenData(BaseModel):
    """Token payload data."""

    username: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[datetime] = None


class TwoFactorSetup(BaseModel):
    """2FA setup response."""

    secret: str
    qr_code_url: str
    backup_codes: List[str]


class DecisionRequest(BaseModel):
    """Decision request from CANDI."""

    analysis_id: str
    incident_id: Optional[str]
    threat_level: str
    source_ip: str
    attributed_actor: Optional[str]
    confidence: float
    iocs: List[str]
    ttps: List[str]
    recommended_actions: List[str]
    forensic_summary: str
    priority: DecisionPriority
    created_at: datetime


class DecisionResponse(BaseModel):
    """Human decision response."""

    decision_id: str
    status: DecisionStatus
    approved_actions: List[ActionType]
    notes: str
    decided_by: str
    decided_at: datetime
    escalation_reason: Optional[str] = None


class DecisionCreate(BaseModel):
    """Create decision response."""

    decision_id: str
    status: DecisionStatus
    approved_actions: List[ActionType]
    notes: str
    escalation_reason: Optional[str] = None


class DecisionStats(BaseModel):
    """Decision statistics."""

    total_pending: int
    critical_pending: int
    high_pending: int
    medium_pending: int
    low_pending: int
    total_completed: int
    avg_response_time_minutes: float
    decisions_last_24h: int
