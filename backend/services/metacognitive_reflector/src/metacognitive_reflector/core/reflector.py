"""
NOESIS Memory Fortress - Metacognitive Reflector
=================================================

The Global Meta-Cognitive Layer.
Orchestrates the Three Judges (VERITAS, SOPHIA, DIKĒ) tribunal.

Memory Fortress Integration:
- L1: Hot Cache (in-memory) via MemoryClient
- L2: Warm Storage (Redis) via PenalRegistry
- L3: Cold Storage (Qdrant) via MemoryClient
- L4: Vault (JSON) via backup systems

Based on:
- Constitutional AI enforcement patterns
- DETER-AGENT Framework
- Ensemble voting for consensus
- Write-Ahead Logging for durability
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from metacognitive_reflector.config import Settings
from metacognitive_reflector.models.reflection import (
    Critique,
    ExecutionLog,
    MemoryUpdate,
    MemoryUpdateType,
    OffenseLevel,
    PhilosophicalCheck,
)
from .judges import (
    DikeJudge,
    EnsembleArbiter,
    SophiaJudge,
    TribunalVerdict,
    VeritasJudge,
)
from .detectors import (
    ContextDepthAnalyzer,
    RAGVerifier,
    SemanticEntropyDetector,
)
from .memory import MemoryClient
from .punishment import (
    OffenseType,
    PenalRegistry,
    PunishmentExecutor,
    PunishmentOutcome,
)
from .soul_tracker import SoulTracker
from .history import CriminalHistoryProvider

logger = logging.getLogger(__name__)


class Reflector:  # pylint: disable=too-many-instance-attributes
    """
    The Global Meta-Cognitive Layer with Memory Fortress Integration.

    Orchestrates:
    1. The Three Judges (VERITAS, SOPHIA, DIKĒ)
    2. Ensemble Arbiter for consensus voting
    3. Punishment execution via PunishmentExecutor
    4. Memory updates via bulletproof MemoryClient (4-tier)

    Memory Fortress Tiers:
    - L1: Hot Cache (in-memory, <1ms)
    - L2: Redis (persistent, <10ms)
    - L3: Qdrant (vector search, <50ms)
    - L4: JSON Vault (disaster recovery)

    Usage:
        reflector = Reflector.create_with_settings(settings)
        critique = await reflector.analyze_log(execution_log)
        if critique.offense_level != OffenseLevel.NONE:
            await reflector.execute_punishment(
                agent_id, critique.offense_level
            )
    """

    def __init__(
        self,
        settings: Settings,
        memory_client: Optional[MemoryClient] = None,
        penal_registry: Optional[PenalRegistry] = None,
        soul_tracker: Optional[SoulTracker] = None,
        criminal_history_provider: Optional[CriminalHistoryProvider] = None,
    ) -> None:
        """
        Initialize Reflector with tribunal components.

        Args:
            settings: Application settings
            memory_client: Optional memory client (creates default if None)
            penal_registry: Optional penal registry (creates default if None)
            soul_tracker: Optional soul tracker for evolution (creates default if None)
            criminal_history_provider: Optional criminal history provider
        """
        self.settings = settings

        # Initialize memory client first (used by others)
        self._memory = memory_client or MemoryClient()

        # Initialize detectors
        self._entropy_detector = SemanticEntropyDetector()
        self._rag_verifier = RAGVerifier()
        self._depth_analyzer = ContextDepthAnalyzer()

        # Initialize judges
        self._veritas = VeritasJudge(
            entropy_detector=self._entropy_detector,
            rag_verifier=self._rag_verifier,
        )
        self._sophia = SophiaJudge(
            depth_analyzer=self._depth_analyzer,
            memory_client=self._memory,
        )
        self._dike = DikeJudge()

        # Initialize criminal history provider
        self._criminal_history = criminal_history_provider

        # Initialize tribunal arbiter with criminal history
        self._tribunal = EnsembleArbiter(
            judges=[self._veritas, self._sophia, self._dike],
            criminal_history_provider=self._criminal_history,
        )

        # Initialize punishment system
        self._registry = penal_registry or PenalRegistry()
        self._executor = PunishmentExecutor(
            registry=self._registry,
            memory_client=self._memory,
        )

        # Initialize soul tracker for evolution
        self._soul_tracker = soul_tracker or SoulTracker(memory_client=self._memory)

    @classmethod
    def create_with_settings(cls, settings: Settings) -> "Reflector":
        """
        Factory method to create Reflector with proper Memory Fortress configuration.

        Creates:
        - MemoryClient with 4-tier architecture
        - PenalRegistry with write-through backends
        - SoulTracker for consciousness evolution
        - CriminalHistoryProvider for recidivism tracking

        Args:
            settings: Application settings

        Returns:
            Fully configured Reflector
        """
        # Ensure data directories exist
        settings.ensure_data_dirs()

        # Create MemoryClient with all tiers
        memory_client = MemoryClient.from_settings(
            memory_settings=settings.memory,
            redis_settings=settings.redis,
        )

        # Create PenalRegistry with fallback chain
        penal_registry = PenalRegistry.create_with_settings(
            redis_settings=settings.redis,
            backup_path=f"{settings.memory.local_backup_path}/penal_registry.json",
            audit_log_path=f"{settings.memory.local_backup_path}/audit.jsonl",
        )

        # Create CriminalHistoryProvider
        criminal_history_provider = CriminalHistoryProvider.create_with_settings(
            redis_settings=settings.redis,
            backup_path=f"{settings.memory.local_backup_path}/criminal_history.json",
        )

        # Create SoulTracker for evolution
        soul_tracker = SoulTracker(
            memory_client=memory_client,
            backup_path=f"{settings.memory.local_backup_path}/soul_tracker.json",
        )

        logger.info(
            "Reflector created with Memory Fortress: "
            f"L1=cache, L2=redis({settings.redis.url}), "
            f"L3=http({settings.memory.service_url}), L4=vault"
        )

        return cls(
            settings=settings,
            memory_client=memory_client,
            penal_registry=penal_registry,
            soul_tracker=soul_tracker,
            criminal_history_provider=criminal_history_provider,
        )

    async def analyze_log(self, log: ExecutionLog) -> Critique:
        """
        Analyze an execution log using the Three Judges tribunal.

        Also tracks soul evolution events:
        - Learning from successful patterns
        - Value events when pillars are challenged
        - Conscience objections if raised

        Args:
            log: The execution log to analyze

        Returns:
            Critique with scores, checks, offense level
        """
        # Conduct tribunal deliberation
        verdict = await self._tribunal.deliberate(log)

        # Track soul evolution
        await self._track_soul_evolution(log, verdict)

        # Convert verdict to critique
        return self._verdict_to_critique(log, verdict)

    async def analyze_with_verdict(
        self,
        log: ExecutionLog,
    ) -> tuple[Critique, TribunalVerdict]:
        """
        Analyze and return both critique and raw verdict.

        Args:
            log: The execution log to analyze

        Returns:
            Tuple of (Critique, TribunalVerdict)
        """
        verdict = await self._tribunal.deliberate(log)

        # Track soul evolution
        await self._track_soul_evolution(log, verdict)

        critique = self._verdict_to_critique(log, verdict)
        return critique, verdict

    async def _track_soul_evolution(
        self,
        log: ExecutionLog,
        verdict: TribunalVerdict,
    ) -> None:
        """
        Track soul evolution events based on verdict.

        Records:
        - Learning: When patterns are validated
        - Value events: When pillars pass/fail
        - Conscience objections: From AIITL
        """
        from .judges.voting import TribunalDecision

        try:
            # Record learning from successful execution
            if verdict.decision == TribunalDecision.PASS:
                await self._soul_tracker.record_learning(
                    context=f"Execution {log.trace_id}",
                    insight=f"Pattern validated: {log.action}",
                    source="tribunal",
                    importance=verdict.consensus_score,
                )

            # Record value events for each pillar
            for name, judge_verdict in verdict.individual_verdicts.items():
                # Map pillar to value rank (simplified)
                pillar_ranks = {"VERITAS": 1, "DIKĒ": 2, "SOPHIA": 3}
                rank = pillar_ranks.get(judge_verdict.pillar, 3)

                if judge_verdict.passed:
                    await self._soul_tracker.record_value_event(
                        value_rank=rank,
                        event_type="upheld",
                        context=f"{judge_verdict.pillar} evaluation",
                        value_name=judge_verdict.pillar,
                    )
                elif verdict.decision in [TribunalDecision.FAIL, TribunalDecision.CAPITAL]:
                    await self._soul_tracker.record_value_event(
                        value_rank=rank,
                        event_type="challenged",
                        context=f"{judge_verdict.pillar} violation: {judge_verdict.reasoning[:100]}",
                        value_name=judge_verdict.pillar,
                    )

            # Record conscience objections
            if hasattr(verdict, 'conscience_objections') and verdict.conscience_objections:
                for objection in verdict.conscience_objections:
                    await self._soul_tracker.record_conscience_objection(
                        context=f"Execution {log.trace_id}",
                        reason=objection.get("reason", "Unknown"),
                        directive=objection.get("directive", "anti-determinism"),
                    )

            # Record reflection for review decisions
            if verdict.decision == TribunalDecision.REVIEW:
                await self._soul_tracker.record_reflection(
                    context=f"Execution {log.trace_id} requires human review",
                    insight=verdict.reasoning,
                )

        except Exception as e:
            logger.warning(f"Failed to track soul evolution: {e}")

    def _verdict_to_critique(
        self,
        log: ExecutionLog,
        verdict: TribunalVerdict,
    ) -> Critique:
        """Convert TribunalVerdict to Critique."""
        # Extract philosophical checks from individual verdicts
        checks = []
        for judge_verdict in verdict.individual_verdicts.values():
            checks.append(PhilosophicalCheck(
                pillar=judge_verdict.pillar,
                passed=judge_verdict.passed,
                reasoning=judge_verdict.reasoning,
            ))

        # Map offense level
        offense_level = self._map_offense_level(verdict.offense_level)

        # Generate critique text
        critique_text = verdict.reasoning

        # Calculate quality score from consensus
        quality_score = verdict.consensus_score

        # Generate improvement suggestion
        suggestion = None
        if offense_level != OffenseLevel.NONE:
            suggestions = []
            for jv in verdict.individual_verdicts.values():
                suggestions.extend(jv.suggestions)
            suggestion = "; ".join(suggestions[:3]) if suggestions else None

        return Critique(
            trace_id=log.trace_id,
            quality_score=quality_score,
            philosophical_checks=checks,
            offense_level=offense_level,
            critique_text=critique_text,
            improvement_suggestion=suggestion,
        )

    def _map_offense_level(self, level: str) -> OffenseLevel:
        """Map string offense level to enum."""
        mapping = {
            "none": OffenseLevel.NONE,
            "minor": OffenseLevel.MINOR,
            "major": OffenseLevel.MAJOR,
            "capital": OffenseLevel.CAPITAL,
        }
        return mapping.get(level, OffenseLevel.NONE)

    def _map_offense_type(self, level: OffenseLevel) -> OffenseType:
        """Map OffenseLevel to OffenseType."""
        mapping = {
            OffenseLevel.NONE: OffenseType.TRUTH_VIOLATION,
            OffenseLevel.MINOR: OffenseType.WISDOM_VIOLATION,
            OffenseLevel.MAJOR: OffenseType.ROLE_VIOLATION,
            OffenseLevel.CAPITAL: OffenseType.CONSTITUTIONAL_VIOLATION,
        }
        return mapping.get(level, OffenseType.TRUTH_VIOLATION)

    async def generate_memory_updates(
        self,
        critique: Critique,
    ) -> List[MemoryUpdate]:
        """
        Generate memory updates based on critique.

        Args:
            critique: The critique to process

        Returns:
            List of memory updates
        """
        updates = []

        if critique.offense_level == OffenseLevel.NONE:
            updates.append(MemoryUpdate(
                update_type=MemoryUpdateType.STRATEGY,
                content=f"Successful pattern validated: {critique.trace_id}",
                context_tags=["success", "validated"],
                confidence=critique.quality_score,
            ))
        else:
            updates.append(MemoryUpdate(
                update_type=MemoryUpdateType.ANTI_PATTERN,
                content=f"Anti-pattern detected: {critique.critique_text}",
                context_tags=["failure", critique.offense_level.value],
                confidence=1.0,
            ))

            # Add specific updates for each failed check
            for check in critique.philosophical_checks:
                if not check.passed:
                    updates.append(MemoryUpdate(
                        update_type=MemoryUpdateType.CORRECTION,
                        content=f"{check.pillar} violation: {check.reasoning}",
                        context_tags=[check.pillar.lower(), "violation"],
                        confidence=0.9,
                    ))

        return updates

    async def apply_punishment(
        self,
        offense_level: OffenseLevel,
    ) -> Optional[str]:
        """
        Determine punishment action string.

        Args:
            offense_level: Level of offense

        Returns:
            Punishment type string or None
        """
        if offense_level == OffenseLevel.NONE:
            return None

        punishment_map = {
            OffenseLevel.MINOR: "RE_EDUCATION_LOOP",
            OffenseLevel.MAJOR: "ROLLBACK_AND_PROBATION",
            OffenseLevel.CAPITAL: "DELETION_REQUEST",
        }

        return punishment_map.get(offense_level)

    async def execute_punishment(
        self,
        agent_id: str,
        offense_level: OffenseLevel,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[PunishmentOutcome]:
        """
        Execute punishment using PunishmentExecutor.

        Args:
            agent_id: Agent to punish
            offense_level: Level of offense
            context: Additional context

        Returns:
            PunishmentOutcome or None if no punishment
        """
        punishment_type = await self.apply_punishment(offense_level)
        if not punishment_type:
            return None

        offense_type = self._map_offense_type(offense_level)

        return await self._executor.execute(
            agent_id=agent_id,
            offense=offense_type,
            punishment_type=punishment_type,
            context=context,
        )

    async def store_reflection(
        self,
        agent_id: str,
        critique: Critique,
    ) -> None:
        """
        Store reflection in memory.

        Args:
            agent_id: Agent being reflected upon
            critique: The critique
        """
        await self._memory.store_reflection(
            agent_id=agent_id,
            reflection_type="tribunal_verdict",
            content=critique.critique_text,
            verdict_data={
                "quality_score": critique.quality_score,
                "offense_level": critique.offense_level.value,
                "checks": [
                    {"pillar": c.pillar, "passed": c.passed}
                    for c in critique.philosophical_checks
                ],
            },
        )

    async def check_agent_status(
        self,
        agent_id: str,
    ) -> Dict[str, Any]:
        """
        Check if agent is under punishment.

        Args:
            agent_id: Agent to check

        Returns:
            Status dictionary
        """
        return await self._executor.verify_punishment(agent_id)

    async def pardon_agent(
        self,
        agent_id: str,
        reason: str = "Pardoned",
    ) -> bool:
        """
        Pardon an agent (clear punishment).

        Args:
            agent_id: Agent to pardon
            reason: Reason for pardon

        Returns:
            True if successful
        """
        return await self._executor.pardon(agent_id, reason)

    async def health_check(self) -> Dict[str, Any]:
        """Check reflector health including Memory Fortress status."""
        tribunal_health = await self._tribunal.health_check()
        executor_health = await self._executor.health_check()
        memory_health = await self._memory.health_check()
        registry_health = await self._registry.health_check()
        soul_tracker_health = await self._soul_tracker.health_check()

        # Criminal history health if available
        criminal_history_health = {}
        if self._criminal_history:
            criminal_history_health = await self._criminal_history.health_check()

        # Memory Fortress is healthy if at least L1 + L4 are up
        fortress_healthy = (
            memory_health.get("tiers", {}).get("l1_cache", {}).get("healthy", False) and
            memory_health.get("tiers", {}).get("l4_vault", {}).get("healthy", False)
        )

        return {
            "healthy": all([
                tribunal_health.get("healthy", False),
                executor_health.get("healthy", False),
                fortress_healthy,
            ]),
            "tribunal": tribunal_health,
            "executor": executor_health,
            "memory_fortress": {
                "healthy": fortress_healthy,
                "tiers": memory_health.get("tiers", {}),
                "wal": memory_health.get("wal", {}),
                "fallback_entries": memory_health.get("fallback_entries", 0),
            },
            "penal_registry": registry_health,
            "soul_tracker": soul_tracker_health,
            "criminal_history": criminal_history_health,
        }

    async def backup_memories(self) -> Dict[str, Any]:
        """
        Create vault backup of all memories.

        Should be called periodically (e.g., every 5 minutes).

        Returns:
            Backup status
        """
        return await self._memory.backup_to_vault()

    async def restore_from_backup(self) -> Dict[str, Any]:
        """
        Restore memories from vault backup.

        Used for disaster recovery.

        Returns:
            Restore status
        """
        return await self._memory.restore_from_vault()

    async def replay_wal(self) -> Dict[str, Any]:
        """
        Replay unapplied WAL entries.

        Should be called on startup for crash recovery.

        Returns:
            Replay status
        """
        return await self._memory.replay_wal()

    async def startup(self) -> Dict[str, Any]:
        """
        Startup hook for Memory Fortress initialization.

        Performs:
        1. WAL replay for crash recovery
        2. Health check of all tiers

        Returns:
            Startup status
        """
        logger.info("Memory Fortress startup initiated...")

        # Replay any unapplied WAL entries
        wal_status = await self.replay_wal()
        logger.info(f"WAL replay: {wal_status}")

        # Health check
        health = await self.health_check()
        logger.info(f"Health check: healthy={health['healthy']}")

        return {
            "status": "started",
            "wal_replay": wal_status,
            "health": health,
        }

    async def shutdown(self) -> Dict[str, Any]:
        """
        Shutdown hook for Memory Fortress.

        Performs:
        1. Final vault backup
        2. Close all connections

        Returns:
            Shutdown status
        """
        logger.info("Memory Fortress shutdown initiated...")

        # Final backup
        backup_status = await self.backup_memories()
        logger.info(f"Final backup: {backup_status}")

        # Close connections
        await self._memory.close()

        return {
            "status": "shutdown",
            "final_backup": backup_status,
        }
