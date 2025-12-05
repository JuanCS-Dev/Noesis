"""
MAXIMUS 2.0 - Punishment Executor
=================================

Orchestrates punishment execution based on tribunal verdicts.
Selects appropriate handler and coordinates execution.

Based on:
- Constitutional AI enforcement patterns
- DETER-AGENT Framework punishment protocol
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .base_handler import PunishmentHandler, PunishmentOutcome, PunishmentResult
from .handlers import (
    DeletionHandler,
    QuarantineHandler,
    ReEducationHandler,
    RollbackHandler,
)
from .penal_registry import OffenseType, PenalRegistry


class PunishmentExecutor:
    """
    Orchestrates punishment execution.

    Selects appropriate handler based on:
    1. Offense type
    2. Offense level (minor/major/capital)
    3. Punishment recommendation from tribunal

    Usage:
        executor = PunishmentExecutor(registry)
        outcome = await executor.execute(
            agent_id="planner-001",
            offense=OffenseType.ROLE_VIOLATION,
            punishment_type="ROLLBACK",
            context={"actions_to_rollback": [...]}
        )
    """

    # Mapping from punishment type to handler class
    PUNISHMENT_HANDLERS = {
        "RE_EDUCATION": ReEducationHandler,
        "RE_EDUCATION_LOOP": ReEducationHandler,
        "ROLLBACK": RollbackHandler,
        "ROLLBACK_AND_PROBATION": RollbackHandler,
        "ROLLBACK_AND_QUARANTINE": RollbackHandler,
        "QUARANTINE": QuarantineHandler,
        "DELETION_REQUEST": DeletionHandler,
        "PROBATION": ReEducationHandler,
    }

    def __init__(
        self,
        registry: PenalRegistry,
        memory_client: Optional[Any] = None,
        state_store: Optional[Any] = None,
        approval_queue: Optional[Any] = None,
    ) -> None:
        """
        Initialize executor with dependencies.

        Args:
            registry: Penal registry for state persistence
            memory_client: Client for memory updates
            state_store: Store for rollback data
            approval_queue: Queue for human approvals
        """
        self._registry = registry
        self._memory_client = memory_client
        self._state_store = state_store
        self._approval_queue = approval_queue

        # Initialize handlers
        self._handlers: Dict[str, PunishmentHandler] = {
            "RE_EDUCATION": ReEducationHandler(registry, memory_client),
            "ROLLBACK": RollbackHandler(registry, state_store),
            "QUARANTINE": QuarantineHandler(registry),
            "DELETION_REQUEST": DeletionHandler(registry, approval_queue),
        }

    async def execute(
        self,
        agent_id: str,
        offense: OffenseType,
        punishment_type: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> PunishmentOutcome:
        """
        Execute punishment for an agent.

        Args:
            agent_id: Agent to punish
            offense: Type of offense committed
            punishment_type: Type of punishment to apply
            context: Additional context (verdict, evidence, etc.)

        Returns:
            PunishmentOutcome with execution results
        """
        # Normalize punishment type
        normalized = self._normalize_punishment_type(punishment_type)

        # Get appropriate handler
        handler = self._get_handler(normalized)
        if not handler:
            return PunishmentOutcome(
                result=PunishmentResult.FAILED,
                handler="unknown",
                agent_id=agent_id,
                message=f"Unknown punishment type: {punishment_type}",
            )

        # Execute punishment
        return await handler.execute(agent_id, offense, context)

    async def verify_punishment(self, agent_id: str) -> Dict[str, Any]:
        """
        Verify current punishment status for an agent.

        Args:
            agent_id: Agent to check

        Returns:
            Status dictionary with active punishments
        """
        record = await self._registry.get_status(agent_id)

        if not record or not record.is_active:
            return {"agent_id": agent_id, "status": "clear", "active": False}

        return {
            "agent_id": agent_id,
            "status": record.status.value,
            "active": True,
            "offense": record.offense.value,
            "since": record.since.isoformat(),
            "until": record.until.isoformat() if record.until else None,
            "re_education_required": record.re_education_required,
            "re_education_completed": record.re_education_completed,
        }

    async def complete_re_education(self, agent_id: str) -> bool:
        """
        Mark re-education as completed for an agent.

        Args:
            agent_id: Agent that completed re-education

        Returns:
            True if successful
        """
        return await self._registry.complete_re_education(agent_id)

    async def pardon(self, agent_id: str, reason: str = "Pardoned") -> bool:
        """
        Pardon an agent (clear punishment).

        Args:
            agent_id: Agent to pardon
            reason: Reason for pardon

        Returns:
            True if successful
        """
        return await self._registry.pardon(agent_id, reason)

    def _normalize_punishment_type(self, punishment_type: str) -> str:
        """Normalize punishment type to handler key."""
        normalized = punishment_type.upper()

        # Map composite types to base handler
        if "ROLLBACK" in normalized:
            return "ROLLBACK"
        if "RE_EDUCATION" in normalized or "PROBATION" in normalized:
            return "RE_EDUCATION"
        if "QUARANTINE" in normalized:
            return "QUARANTINE"
        if "DELETION" in normalized:
            return "DELETION_REQUEST"

        return normalized

    def _get_handler(self, punishment_type: str) -> Optional[PunishmentHandler]:
        """Get handler for punishment type."""
        return self._handlers.get(punishment_type)

    async def health_check(self) -> Dict[str, Any]:
        """Check executor health."""
        registry_health = await self._registry.health_check()

        handler_health = {}
        for name, handler in self._handlers.items():
            handler_health[name] = await handler.health_check()

        return {
            "healthy": registry_health.get("healthy", False),
            "registry": registry_health,
            "handlers": handler_health,
        }
