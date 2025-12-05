"""
MAXIMUS 2.0 - Metacognitive Reflector
======================================

The Global Meta-Cognitive Layer.
Orchestrates the Three Judges (VERITAS, SOPHIA, DIKĒ) tribunal.

Based on:
- Constitutional AI enforcement patterns
- DETER-AGENT Framework
- Ensemble voting for consensus
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..config import Settings
from ..models.reflection import (
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
from .memory_client import MemoryClient
from .punishment import (
    OffenseType,
    PenalRegistry,
    PunishmentExecutor,
    PunishmentOutcome,
)


class Reflector:  # pylint: disable=too-many-instance-attributes
    """
    The Global Meta-Cognitive Layer.

    Orchestrates:
    1. The Three Judges (VERITAS, SOPHIA, DIKĒ)
    2. Ensemble Arbiter for consensus voting
    3. Punishment execution via PunishmentExecutor
    4. Memory updates via MemoryClient

    Usage:
        reflector = Reflector(settings)
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
    ) -> None:
        """
        Initialize Reflector with tribunal components.

        Args:
            settings: Application settings
            memory_client: Optional memory client (creates default if None)
            penal_registry: Optional penal registry (creates default if None)
        """
        self.settings = settings

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
            memory_client=memory_client,
        )
        self._dike = DikeJudge()

        # Initialize tribunal arbiter
        self._tribunal = EnsembleArbiter(
            judges=[self._veritas, self._sophia, self._dike],
        )

        # Initialize punishment system
        self._registry = penal_registry or PenalRegistry()
        self._executor = PunishmentExecutor(
            registry=self._registry,
            memory_client=memory_client,
        )

        # Initialize memory client
        self._memory = memory_client or MemoryClient()

    async def analyze_log(self, log: ExecutionLog) -> Critique:
        """
        Analyze an execution log using the Three Judges tribunal.

        Args:
            log: The execution log to analyze

        Returns:
            Critique with scores, checks, offense level
        """
        # Conduct tribunal deliberation
        verdict = await self._tribunal.deliberate(log)

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
        critique = self._verdict_to_critique(log, verdict)
        return critique, verdict

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
        """Check reflector health."""
        tribunal_health = await self._tribunal.health_check()
        executor_health = await self._executor.health_check()
        memory_health = await self._memory.health_check()

        return {
            "healthy": all([
                tribunal_health.get("healthy", False),
                executor_health.get("healthy", False),
                memory_health.get("healthy", False),
            ]),
            "tribunal": tribunal_health,
            "executor": executor_health,
            "memory": memory_health,
        }
