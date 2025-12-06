"""HITL Backend Package.

Modular FastAPI application for Human-in-the-Loop decision system.

The original hitl_backend.py (942 lines) has been decomposed into:
- models.py: Enums and Pydantic models
- database.py: In-memory database storage
- auth.py: Authentication and authorization
- decisions.py: Decision management endpoints
- websocket_routes.py: WebSocket handling
- app.py: FastAPI application setup
"""

from __future__ import annotations

from .app import app
from .models import (
    ActionType,
    DecisionCreate,
    DecisionPriority,
    DecisionRequest,
    DecisionResponse,
    DecisionStats,
    DecisionStatus,
    Token,
    TokenData,
    TwoFactorSetup,
    UserCreate,
    UserInDB,
    UserRole,
)

__all__ = [
    "app",
    "ActionType",
    "DecisionCreate",
    "DecisionPriority",
    "DecisionRequest",
    "DecisionResponse",
    "DecisionStats",
    "DecisionStatus",
    "Token",
    "TokenData",
    "TwoFactorSetup",
    "UserCreate",
    "UserInDB",
    "UserRole",
]
