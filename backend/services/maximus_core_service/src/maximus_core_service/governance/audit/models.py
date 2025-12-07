"""
Audit Data Models.

Contains audit log models for governance actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from ..enums import AuditLogLevel, GovernanceAction


@dataclass
class AuditLog:
    """Audit log entry for governance actions."""

    log_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    action: GovernanceAction = GovernanceAction.AUDIT_LOG_CREATED
    log_level: AuditLogLevel = AuditLogLevel.INFO
    actor: str = "system"  # User ID or "system"
    target_entity_type: str = ""  # policy, erb_member, meeting, decision
    target_entity_id: str = ""
    description: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    ip_address: str | None = None
    user_agent: str | None = None
    session_id: str | None = None
    correlation_id: str | None = None  # For tracking related events
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "log_id": self.log_id,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value,
            "log_level": self.log_level.value,
            "actor": self.actor,
            "target_entity_type": self.target_entity_type,
            "target_entity_id": self.target_entity_id,
            "description": self.description,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
        }
