"""
MAXIMUS 2.0 - Punishment Handler Base
=====================================

Base classes and models for punishment handlers.
Extracted for CODE_CONSTITUTION compliance (< 500 lines per file).

Contains:
- PunishmentResult: Outcome status enum
- PunishmentOutcome: Result data class
- PunishmentHandler: Abstract base class
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .penal_registry import OffenseType


class PunishmentResult(str, Enum):
    """Result of punishment execution."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    PENDING_APPROVAL = "pending_approval"


@dataclass
class PunishmentOutcome:  # pylint: disable=too-many-instance-attributes
    """
    Outcome of a punishment execution.

    Attributes:
        result: Success/failure status
        handler: Which handler executed
        agent_id: Agent that was punished
        actions_taken: List of actions performed
        rollback_id: ID for potential rollback of rollback
        requires_followup: Whether follow-up is needed
        message: Human-readable message
        metadata: Additional context
    """

    result: PunishmentResult
    handler: str
    agent_id: str
    actions_taken: List[str] = field(default_factory=list)
    rollback_id: Optional[str] = None
    requires_followup: bool = False
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class PunishmentHandler(ABC):
    """
    Abstract base class for punishment handlers.

    Each handler implements a specific punishment type.
    Handlers are stateless; state is managed by PenalRegistry.

    Implementations must provide:
    - punishment_type: Identifier string
    - severity: 1=minor, 2=major, 3=capital
    - execute: Perform the punishment
    - verify: Check if punishment is still active
    """

    @property
    @abstractmethod
    def punishment_type(self) -> str:
        """Type of punishment this handler executes."""

    @property
    @abstractmethod
    def severity(self) -> int:
        """Severity level (1=minor, 2=major, 3=capital)."""

    @abstractmethod
    async def execute(
        self,
        agent_id: str,
        offense: OffenseType,
        context: Optional[Dict[str, Any]] = None,
    ) -> PunishmentOutcome:
        """
        Execute the punishment.

        Args:
            agent_id: Agent to punish
            offense: Type of offense committed
            context: Additional context (verdict, evidence, etc.)

        Returns:
            PunishmentOutcome with results
        """

    @abstractmethod
    async def verify(self, agent_id: str) -> bool:
        """
        Verify punishment is still in effect.

        Args:
            agent_id: Agent to check

        Returns:
            True if punishment is active
        """

    async def health_check(self) -> Dict[str, Any]:
        """Check if handler is operational."""
        return {
            "healthy": True,
            "handler": self.punishment_type,
            "severity": self.severity,
        }
