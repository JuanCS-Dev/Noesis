"""Enums for HITL module."""

from __future__ import annotations

from enum import Enum


class AutomationLevel(Enum):
    """Automation level for AI decisions."""

    FULL = "full"
    SUPERVISED = "supervised"
    ADVISORY = "advisory"
    MANUAL = "manual"


class RiskLevel(Enum):
    """Risk level for security actions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DecisionStatus(Enum):
    """Status of HITL decision in workflow."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"


class ActionType(Enum):
    """Types of security actions that can be automated."""

    ISOLATE_HOST = "isolate_host"
    BLOCK_IP = "block_ip"
    BLOCK_DOMAIN = "block_domain"
    BLOCK_PORT = "block_port"
    THROTTLE_CONNECTION = "throttle_connection"
    RESET_CONNECTION = "reset_connection"
    QUARANTINE_FILE = "quarantine_file"
    DELETE_FILE = "delete_file"
    DELETE_DATA = "delete_data"
    ENCRYPT_DATA = "encrypt_data"
    BACKUP_DATA = "backup_data"
    KILL_PROCESS = "kill_process"
    SUSPEND_PROCESS = "suspend_process"
    DISABLE_USER = "disable_user"
    LOCK_ACCOUNT = "lock_account"
    RESET_PASSWORD = "reset_password"
    COLLECT_FORENSICS = "collect_forensics"
    CAPTURE_MEMORY = "capture_memory"
    SNAPSHOT_VM = "snapshot_vm"
    COLLECT_LOGS = "collect_logs"
    SEND_ALERT = "send_alert"
    CREATE_TICKET = "create_ticket"
    NOTIFY_TEAM = "notify_team"
    ESCALATE_INCIDENT = "escalate_incident"
