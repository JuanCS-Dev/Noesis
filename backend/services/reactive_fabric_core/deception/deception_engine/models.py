"""
Models for Deception Engine.

Enums and Pydantic models for deception elements.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class DeceptionType(Enum):
    """Types of deception elements."""

    HONEYTOKEN = "honeytoken"
    DECOY_SYSTEM = "decoy_system"
    TRAP_DOCUMENT = "trap_document"
    BREADCRUMB = "breadcrumb"
    FAKE_DATA = "fake_data"


class TokenType(Enum):
    """Types of honeytokens."""

    API_KEY = "api_key"
    PASSWORD = "password"
    SSH_KEY = "ssh_key"
    DATABASE_CRED = "database_cred"
    AWS_KEY = "aws_key"
    OAUTH_TOKEN = "oauth_token"
    JWT = "jwt"
    COOKIE = "cookie"


class DeceptionConfig(BaseModel):
    """Configuration for Deception Engine."""

    # Honeytoken settings
    honeytoken_types: List[TokenType] = Field(
        default_factory=lambda: [
            TokenType.API_KEY,
            TokenType.PASSWORD,
            TokenType.DATABASE_CRED
        ],
        description="Types of honeytokens to generate"
    )
    honeytokens_per_type: int = Field(
        default=5, description="Number of honeytokens per type"
    )
    token_rotation_days: int = Field(
        default=30, description="Days before rotating honeytokens"
    )

    # Decoy settings
    max_decoy_systems: int = Field(
        default=10, description="Maximum number of decoy systems"
    )
    decoy_ports: List[int] = Field(
        default_factory=lambda: [22, 80, 443, 3306, 5432],
        description="Ports for decoy services"
    )

    # Trap document settings
    trap_document_types: List[str] = Field(
        default_factory=lambda: ["pdf", "docx", "xlsx", "txt"],
        description="Types of trap documents"
    )
    max_trap_documents: int = Field(
        default=20, description="Maximum trap documents"
    )

    # Monitoring settings
    alert_threshold: int = Field(
        default=1, description="Access count before alerting"
    )
    tracking_enabled: bool = Field(
        default=True, description="Enable access tracking"
    )


class Honeytoken(BaseModel):
    """Represents a honeytoken."""

    token_id: str = Field(default_factory=lambda: str(uuid4()))
    token_type: TokenType
    token_value: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    deployed_locations: List[str] = Field(default_factory=list)
    triggered: bool = False


class DecoySystem(BaseModel):
    """Represents a decoy system or service."""

    decoy_id: str = Field(default_factory=lambda: str(uuid4()))
    hostname: str
    ip_address: str
    services: List[Dict[str, Any]]
    honeytokens: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_interaction: Optional[datetime] = None
    interaction_count: int = 0
    triggered: bool = False


class TrapDocument(BaseModel):
    """Represents a trap document with tracking."""

    document_id: str = Field(default_factory=lambda: str(uuid4()))
    filename: str
    document_type: str
    content_hash: str
    tracking_token: str
    deployed_paths: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    access_log: List[Dict[str, Any]] = Field(default_factory=list)
    triggered: bool = False


class BreadcrumbTrail(BaseModel):
    """Represents a breadcrumb trail for deception."""

    trail_id: str = Field(default_factory=lambda: str(uuid4()))
    trail_type: str
    false_path: str
    real_path: Optional[str] = None
    honeytokens: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    followed: bool = False
    follow_count: int = 0


class DeceptionEvent(BaseModel):
    """Event triggered by deception element interaction."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    deception_type: DeceptionType
    element_id: str
    source_ip: Optional[str] = None
    source_user: Optional[str] = None
    action: str
    severity: str
    details: Dict[str, Any] = Field(default_factory=dict)
