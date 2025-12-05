"""
Models for Honeytoken Manager.

Enums and data classes for honeytokens.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class HoneytokenType(Enum):
    """Types of honeytokens."""

    AWS_CREDENTIALS = "aws_credentials"
    API_TOKEN = "api_token"
    SSH_KEY = "ssh_key"
    DATABASE_CREDS = "database_credentials"
    OAUTH_TOKEN = "oauth_token"
    DOCUMENT = "document"
    COOKIE = "cookie"
    ENVIRONMENT_VAR = "environment_variable"


class HoneytokenStatus(Enum):
    """Status of honeytoken."""

    ACTIVE = "active"
    TRIGGERED = "triggered"
    EXPIRED = "expired"
    REVOKED = "revoked"


class Honeytoken:
    """Represents a single honeytoken."""

    def __init__(
        self,
        token_id: str,
        token_type: HoneytokenType,
        value: str,
        metadata: Dict[str, Any],
    ) -> None:
        """
        Initialize honeytoken.

        Args:
            token_id: Unique identifier
            token_type: Type of honeytoken
            value: The actual token value
            metadata: Additional metadata
        """
        self.token_id = token_id
        self.token_type = token_type
        self.value = value
        self.metadata = metadata
        self.status = HoneytokenStatus.ACTIVE
        self.created_at = datetime.now()
        self.triggered_at: Optional[datetime] = None
        self.trigger_count = 0
        self.trigger_sources: List[str] = []

    def trigger(self, source_ip: str, context: Dict[str, Any]) -> None:
        """Mark token as triggered."""
        self.status = HoneytokenStatus.TRIGGERED
        self.triggered_at = datetime.now()
        self.trigger_count += 1
        self.trigger_sources.append(source_ip)
        self.metadata["last_trigger"] = {
            "source_ip": source_ip,
            "timestamp": self.triggered_at.isoformat(),
            "context": context,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "token_id": self.token_id,
            "token_type": self.token_type.value,
            "value": self.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "triggered_at": (
                self.triggered_at.isoformat() if self.triggered_at else None
            ),
            "trigger_count": self.trigger_count,
            "trigger_sources": self.trigger_sources,
            "metadata": self.metadata,
        }
