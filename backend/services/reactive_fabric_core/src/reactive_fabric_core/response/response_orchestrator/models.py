"""
Models for Response Orchestrator.

Contains Enums and Pydantic models for response actions and plans.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ResponsePriority(str, Enum):
    """Response priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ResponseStatus(str, Enum):
    """Response execution status."""

    PENDING = "pending"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLBACK = "rollback"
    CANCELLED = "cancelled"


class ActionType(str, Enum):
    """Types of response actions."""

    # Network actions
    BLOCK_IP = "block_ip"
    BLOCK_PORT = "block_port"
    ISOLATE_HOST = "isolate_host"
    SEGMENT_NETWORK = "segment_network"

    # Process actions
    KILL_PROCESS = "kill_process"
    SUSPEND_PROCESS = "suspend_process"

    # File actions
    QUARANTINE_FILE = "quarantine_file"
    DELETE_FILE = "delete_file"

    # User actions
    DISABLE_USER = "disable_user"
    REVOKE_ACCESS = "revoke_access"
    FORCE_LOGOUT = "force_logout"

    # System actions
    ACTIVATE_KILL_SWITCH = "activate_kill_switch"
    ENABLE_DATA_DIODE = "enable_data_diode"
    TRIGGER_BACKUP = "trigger_backup"

    # Defensive actions
    DEPLOY_HONEYPOT = "deploy_honeypot"
    UPDATE_FIREWALL = "update_firewall"
    ROTATE_CREDENTIALS = "rotate_credentials"


class ResponseAction(BaseModel):
    """Individual response action."""

    action_id: str = Field(default_factory=lambda: str(uuid4()))
    action_type: ActionType
    target: Dict[str, Any]
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: ResponsePriority
    reversible: bool = True
    requires_approval: bool = True
    timeout_seconds: int = 300
    retry_attempts: int = 3
    rollback_on_failure: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: ResponseStatus = ResponseStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class ResponsePlan(BaseModel):
    """Coordinated response plan."""

    plan_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    threat_id: str
    threat_score: float = Field(ge=0.0, le=1.0)
    actions: List[ResponseAction]
    execution_order: List[str]  # Action IDs in order
    parallel_groups: List[List[str]] = Field(default_factory=list)
    priority: ResponsePriority
    auto_execute: bool = False
    require_confirmation: bool = True
    rollback_plan: Optional[List[str]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: ResponseStatus = ResponseStatus.PENDING
    executed_actions: List[str] = Field(default_factory=list)
    failed_actions: List[str] = Field(default_factory=list)


class SafetyCheck(BaseModel):
    """Safety check before executing actions."""

    check_id: str = Field(default_factory=lambda: str(uuid4()))
    check_type: str
    passed: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = Field(default_factory=dict)


class ResponseConfig(BaseModel):
    """Response orchestrator configuration."""

    auto_response_enabled: bool = False
    max_concurrent_actions: int = 5
    action_timeout_seconds: int = 300
    require_dual_approval: bool = True
    rollback_on_failure: bool = True
    safety_checks_enabled: bool = True
    critical_threshold: float = 0.8
    high_threshold: float = 0.6
    medium_threshold: float = 0.4
    max_retry_attempts: int = 3
    audit_all_actions: bool = True
