"""HITL Backend - Database Storage.

In-memory database for the HITL system.
In production, replace with persistent database.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from passlib.context import CryptContext

from .models import (
    DecisionPriority,
    DecisionRequest,
    DecisionResponse,
    UserInDB,
    UserRole,
)

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class HITLDatabase:
    """In-memory database for HITL system."""

    def __init__(self) -> None:
        """Initialize database with empty collections."""
        self.users: Dict[str, UserInDB] = {}
        self.decisions: Dict[str, DecisionRequest] = {}
        self.responses: Dict[str, DecisionResponse] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.audit_log: List[Dict[str, Any]] = []

        # Create default admin user
        self._create_default_admin()

    def _create_default_admin(self) -> None:
        """Create default admin user for initial setup."""
        admin = UserInDB(
            username="admin",
            email="admin@reactive-fabric.local",
            full_name="System Administrator",
            role=UserRole.ADMIN,
            hashed_password=pwd_context.hash("ChangeMe123!"),
            is_active=True,
            is_2fa_enabled=False,
            created_at=datetime.now(),
        )
        self.users["admin"] = admin
        logger.info("Default admin user created (username: admin, password: ChangeMe123!)")

    def add_user(self, user: UserInDB) -> None:
        """Add user to database."""
        self.users[user.username] = user

    def get_user(self, username: str) -> Optional[UserInDB]:
        """Get user by username."""
        return self.users.get(username)

    def add_decision(self, decision: DecisionRequest) -> None:
        """Add decision request."""
        self.decisions[decision.analysis_id] = decision

    def get_decision(self, analysis_id: str) -> Optional[DecisionRequest]:
        """Get decision request."""
        return self.decisions.get(analysis_id)

    def add_response(self, response: DecisionResponse) -> None:
        """Add decision response."""
        self.responses[response.decision_id] = response

    def get_pending_decisions(
        self, priority: Optional[DecisionPriority] = None
    ) -> List[DecisionRequest]:
        """Get pending decisions sorted by priority and timestamp."""
        pending = [
            d for d in self.decisions.values() if d.analysis_id not in self.responses
        ]

        if priority:
            pending = [d for d in pending if d.priority == priority]

        # Sort by priority and timestamp
        priority_order = {
            DecisionPriority.CRITICAL: 0,
            DecisionPriority.HIGH: 1,
            DecisionPriority.MEDIUM: 2,
            DecisionPriority.LOW: 3,
        }
        pending.sort(key=lambda x: (priority_order[x.priority], x.created_at))

        return pending

    def audit(self, event: str, user: str, details: Dict[str, Any]) -> None:
        """Add audit log entry."""
        self.audit_log.append(
            {
                "timestamp": datetime.now(),
                "event": event,
                "user": user,
                "details": details,
            }
        )


# Global database instance
db = HITLDatabase()
