"""HITL Engine Package.

Human-In-The-Loop engine for managing alerts and decisions.

The original hitl_engine.py (858 lines) has been decomposed into:
- models.py: Enums and Pydantic models
- alerts.py: Alert management mixin
- decisions.py: Decision management mixin
- engine.py: Main HITLEngine class
"""

from __future__ import annotations

from .engine import HITLEngine
from .models import (
    Alert,
    AlertPriority,
    AlertStatus,
    ApprovalStatus,
    AuditLog,
    DecisionRequest,
    DecisionResponse,
    DecisionType,
    HITLConfig,
    WorkflowState,
)

__all__ = [
    "HITLEngine",
    "Alert",
    "AlertPriority",
    "AlertStatus",
    "ApprovalStatus",
    "AuditLog",
    "DecisionRequest",
    "DecisionResponse",
    "DecisionType",
    "HITLConfig",
    "WorkflowState",
]
