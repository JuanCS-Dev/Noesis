"""
Recursive Reasoner - Motor de Raciocínio Recursivo
==================================================

Implementa metacognição através de loops recursivos validados.

Permite que MAXIMUS:
1. Pense sobre seu próprio pensamento (metacognição)
2. Detecte contradições em suas crenças
3. Revise crenças inconsistentes
4. Raciocine em múltiplos níveis de abstração

Exemplo de Recursão:
--------------------
Level 0: "Há uma ameaça no IP 192.168.1.1" (objeto-level)
Level 1: "Eu acredito que há uma ameaça em 192.168.1.1" (meta-level)
Level 2: "Eu acredito que minha crença sobre 192.168.1.1 é justificada" (meta-meta)
Level 3: "Eu acredito que minha meta-crença sobre justificação é coerente"

Baseline Científico:
-------------------
- Carruthers (2009): Higher-Order Thoughts (HOT Theory)
- Hofstadter (1979): Strange Loops e auto-referência
- Graziano (2013, 2019): Attention Schema Theory

Authors: Claude Code + Juan
Version: 1.0.0
Date: 2025-12-02
"""

from __future__ import annotations

import logging
import warnings
from datetime import datetime
from time import perf_counter
from typing import Any, Dict, List, Optional, Set, Tuple, TYPE_CHECKING
from uuid import UUID

from .belief_graph import BeliefGraph
from .belief_models import Belief, BeliefType, ContradictionType, ResolutionStrategy  # Re-export
from .contradiction_detector import BeliefRevision, ContradictionDetector
from .contradiction_models import Contradiction, Resolution
from .introspection_engine import IntrospectionEngine
from .meta_monitor import MetaMonitor
from .reasoning_models import (
    ReasoningLevel,
    ReasoningStep,
    RecursiveReasoningResult,
)

__all__ = [
    "RecursiveReasoner",
    "Belief",
    "BeliefType",
    "ContradictionType",
    "ResolutionStrategy",
    "BeliefRevision",
    "ContradictionDetector",
    "Contradiction",
    "Resolution",
    "ReasoningLevel",
    "ReasoningStep",
    "RecursiveReasoningResult",
]

if TYPE_CHECKING:  # pragma: no cover
    from consciousness.mea.attention_schema import AttentionState
    from consciousness.mea.boundary_detector import BoundaryAssessment
    from consciousness.mea.self_model import IntrospectiveSummary
    from consciousness.episodic_memory import Episode

logger = logging.getLogger(__name__)


class RecursiveReasoner:
    """
    Motor de raciocínio recursivo.

    Permite que MAXIMUS raciocine sobre seu próprio raciocínio
    em múltiplos níveis de abstração.
    """

    def __init__(self, max_depth: int = 3):
        """
        Initialize recursive reasoner.

        Args:
            max_depth: Profundidade máxima de recursão (default 3)
                      1 = simples, 2 = meta, 3+ = meta-meta
        """
        if max_depth < 1:
            raise ValueError("max_depth must be >= 1")
        if max_depth > 5:
            warnings.warn(f"max_depth={max_depth} is high, may be slow", UserWarning)

        self.max_depth = max_depth
        self.belief_graph = BeliefGraph()
        self.reasoning_history: List[ReasoningStep] = []
        self.contradiction_detector = ContradictionDetector()
        self.belief_revision = BeliefRevision()
        self.meta_monitor = MetaMonitor()
        self.introspection_engine = IntrospectionEngine()
        self._seen_contradiction_pairs: Set[Tuple[UUID, UUID]] = set()
        self._mea_attention_state: Optional["AttentionState"] = None
        self._mea_boundary: Optional["BoundaryAssessment"] = None
        self._mea_summary: Optional["IntrospectiveSummary"] = None
        self._episodic_episode: Optional["Episode"] = None
        self._episodic_narrative: Optional[str] = None
        self._episodic_coherence: Optional[float] = None

    async def reason_recursively(
        self, initial_belief: Belief, context: Dict[str, Any]
    ) -> RecursiveReasoningResult:
        """
        Executa raciocínio recursivo sobre uma crença inicial.

        Process:
            1. Avaliar crença de nível 0 (objeto-level)
            2. Para cada nível até max_depth:
                a. Gerar meta-crença sobre nível anterior
                b. Avaliar justificação da meta-crença
                c. Detectar contradições
                d. Revisar se necessário
            3. Retornar resultado com todos os níveis

        Args:
            initial_belief: Crença inicial (nível 0)
            context: Contexto adicional para raciocínio

        Returns:
            RecursiveReasoningResult com todos os níveis de raciocínio
        """
        start_time = perf_counter()
        levels: List[ReasoningLevel] = []
        current_belief = initial_belief
        contradictions_detected: List[Contradiction] = []
        resolutions_applied: List[Resolution] = []

        self._integrate_mea_context(context)

        # Adicionar crença inicial ao grafo
        self.belief_graph.add_belief(initial_belief)

        for depth in range(self.max_depth + 1):
            logger.debug(f"Reasoning at level {depth}")

            # Raciocínio neste nível
            level_result = await self._reason_at_level(
                belief=current_belief, depth=depth, context=context
            )
            levels.append(level_result)
            self._register_level_beliefs(level_result)

            # Detectar contradições nível a nível utilizando detector avançado
            contradictions = await self.contradiction_detector.detect_contradictions(
                self.belief_graph
            )
            new_contradictions: List[Contradiction] = []
            for contradiction in contradictions:
                pair = self._contradiction_pair(contradiction)
                if pair in self._seen_contradiction_pairs:
                    continue
                self._seen_contradiction_pairs.add(pair)
                new_contradictions.append(contradiction)

            for contradiction in new_contradictions:
                contradictions_detected.append(contradiction)

                # Resolver contradições seguindo revisão AGM
                outcome = await self.belief_revision.revise_belief_graph(
                    self.belief_graph, contradiction
                )
                resolutions_applied.append(outcome.resolution)

            # Gerar meta-crença para próximo nível
            if depth < self.max_depth:
                current_belief = self._generate_meta_belief(level_result, depth + 1)
                self.belief_graph.add_belief(current_belief)

        # Calcular coerência global
        coherence_score = self._calculate_coherence(levels)
        duration_ms = (perf_counter() - start_time) * 1000.0

        result = RecursiveReasoningResult(
            levels=levels,
            final_depth=len(levels),
            coherence_score=coherence_score,
            contradictions_detected=contradictions_detected,
            resolutions_applied=resolutions_applied,
            timestamp=datetime.now(),
            duration_ms=duration_ms,
        )
        result.meta_report = self.meta_monitor.monitor_reasoning(result)
        result.introspection_report = self.introspection_engine.generate_introspection_report(
            result
        )
        result.attention_state = self._mea_attention_state
        result.boundary_assessment = self._mea_boundary
        result.self_summary = self._mea_summary
        result.episodic_episode = self._episodic_episode
        result.episodic_narrative = self._episodic_narrative
        result.episodic_coherence = self._episodic_coherence
        return result

    async def _reason_at_level(
        self, belief: Belief, depth: int, context: Dict[str, Any]
    ) -> ReasoningLevel:
        """
        Executa raciocínio em um nível específico.

        Args:
            belief: Crença a processar
            depth: Profundidade atual
            context: Contexto

        Returns:
            ReasoningLevel com resultados deste nível
        """
        steps: List[ReasoningStep] = []
        beliefs: List[Belief] = [belief]

        # Avaliar justificação da crença
        justification_chain = self._build_justification_chain(belief)

        # Avaliar confiança
        confidence_assessment = self._assess_confidence(belief, justification_chain)

        step = ReasoningStep(
            belief=belief,
            meta_level=depth,
            justification_chain=justification_chain,
            confidence_assessment=confidence_assessment,
        )
        steps.append(step)
        self.reasoning_history.append(step)

        # Calcular coerência do nível
        level_coherence = self._calculate_level_coherence(beliefs, steps)

        return ReasoningLevel(level=depth, beliefs=beliefs, coherence=level_coherence, steps=steps)

    def _build_justification_chain(self, belief: Belief) -> List[Belief]:
        """Constrói cadeia de justificações para crença."""
        if not belief.justification:
            return []

        chain = list(belief.justification)

        # Recursivamente adicionar justificações das justificações
        for justifying_belief in belief.justification:
            chain.extend(self._build_justification_chain(justifying_belief))

        return chain

    def _assess_confidence(self, belief: Belief, justification_chain: List[Belief]) -> float:
        """
        Avalia confiança calibrada para crença.

        Heurística:
        - Se sem justificação: manter confiança original
        - Se com justificação: média ponderada com justificações
        """
        if not justification_chain:
            return belief.confidence

        # Média das confianças das justificações
        avg_justification_conf = sum(b.confidence for b in justification_chain) / len(
            justification_chain
        )

        # Média ponderada (70% crença, 30% justificações)
        return 0.7 * belief.confidence + 0.3 * avg_justification_conf

    def _calculate_level_coherence(
        self, beliefs: List[Belief], steps: List[ReasoningStep]
    ) -> float:
        """Calcula coerência interna de um nível."""
        if not beliefs:
            return 1.0

        # Simplificação: usar coerência do grafo
        return self.belief_graph.calculate_coherence()

    def _register_level_beliefs(self, level_result: ReasoningLevel) -> None:
        """Assegura que crenças derivadas sejam persistidas no grafo."""
        for belief in level_result.beliefs:
            if (
                belief not in self.belief_graph.beliefs
            ):  # pragma: no cover - beliefs registered via reason_recursively line 673
                justification = (
                    belief.justification if belief.justification else None
                )  # pragma: no cover
                self.belief_graph.add_belief(
                    belief, justification=justification
                )  # pragma: no cover

    @staticmethod
    def _contradiction_pair(contradiction: Contradiction) -> Tuple[UUID, UUID]:
        """Cria identificador estável para contradições baseado nas crenças."""
        ordered = sorted(
            [contradiction.belief_a.id, contradiction.belief_b.id],
            key=lambda value: value.hex,
        )
        return ordered[0], ordered[1]

    def _integrate_mea_context(self, context: Dict[str, Any]) -> None:
        """Seed belief graph with MEA context (attention + boundary + self narrative)."""
        attention_state = context.get("mea_attention_state")
        boundary = context.get("mea_boundary")
        summary = context.get("mea_summary")
        episodic_episode = context.get("episodic_episode")
        episodic_narrative = context.get("episodic_narrative")
        episodic_coherence = context.get("episodic_coherence")

        from consciousness.mea.attention_schema import (
            AttentionState,
        )  # local import to avoid heavy dependencies
        from consciousness.mea.boundary_detector import BoundaryAssessment
        from consciousness.mea.self_model import IntrospectiveSummary
        from consciousness.episodic_memory import Episode

        if isinstance(attention_state, AttentionState):
            self._mea_attention_state = attention_state

            focus_content = (
                f"Current attentional focus is '{attention_state.focus_target}' "
                f"with confidence {attention_state.confidence:.2f}"
            )
            focus_belief = Belief(
                content=focus_content,
                belief_type=BeliefType.FACTUAL,
                confidence=attention_state.confidence,
                context={"source": "MEA", "type": "attention_focus"},
                meta_level=0,
            )
            self.belief_graph.add_belief(focus_belief)

            for modality, weight in attention_state.modality_weights.items():
                modality_belief = Belief(
                    content=f"Attention modality '{modality}' weight {weight:.2f}",
                    belief_type=BeliefType.FACTUAL,
                    confidence=weight,
                    context={"source": "MEA", "type": "attention_modality"},
                    meta_level=0,
                )
                self.belief_graph.add_belief(modality_belief)

        if isinstance(boundary, BoundaryAssessment):
            self._mea_boundary = boundary

            boundary_content = f"Ego boundary strength {boundary.strength:.2f} and stability {boundary.stability:.2f}"
            boundary_belief = Belief(
                content=boundary_content,
                belief_type=BeliefType.FACTUAL,
                confidence=boundary.stability,
                context={"source": "MEA", "type": "boundary"},
                meta_level=0,
            )
            self.belief_graph.add_belief(boundary_belief)

        if isinstance(summary, IntrospectiveSummary):
            self._mea_summary = summary

            narrative_belief = Belief(
                content=f"Self-narrative reports: {summary.narrative}",
                belief_type=BeliefType.META,
                confidence=summary.confidence,
                context={"source": "MEA", "type": "self_report"},
                meta_level=1,
            )
            self.belief_graph.add_belief(narrative_belief)

        if isinstance(episodic_episode, Episode):
            self._episodic_episode = episodic_episode
            episodic_content = (
                f"Episodic episode at {episodic_episode.timestamp.isoformat(timespec='seconds')} "
                f"focused on '{episodic_episode.focus_target}'"
            )
            episodic_belief = Belief(
                content=episodic_content,
                belief_type=BeliefType.FACTUAL,
                confidence=episodic_episode.confidence,
                context={"source": "EpisodicMemory", "episode_id": episodic_episode.episode_id},
                meta_level=0,
            )
            self.belief_graph.add_belief(episodic_belief)

        if isinstance(episodic_narrative, str) and episodic_coherence is not None:
            self._episodic_narrative = episodic_narrative
            self._episodic_coherence = float(episodic_coherence)
            coherence = float(episodic_coherence)
            narrative_belief = Belief(
                content=f"Episodic narrative summary: {episodic_narrative}",
                belief_type=BeliefType.META,
                confidence=max(0.0, min(1.0, coherence)),
                context={"source": "EpisodicMemory", "type": "narrative"},
                meta_level=1,
            )
            self.belief_graph.add_belief(narrative_belief)
        else:
            if isinstance(episodic_narrative, str):
                self._episodic_narrative = episodic_narrative
            if isinstance(episodic_coherence, (int, float)):
                self._episodic_coherence = float(episodic_coherence)

    def _generate_meta_belief(self, level_result: ReasoningLevel, next_level: int) -> Belief:
        """
        Gera meta-crença sobre nível de raciocínio.

        Args:
            level_result: Resultado do nível anterior
            next_level: Nível da nova meta-crença

        Returns:
            Meta-crença de ordem superior
        """
        base_belief = level_result.beliefs[0]

        meta_content = f"I believe that '{base_belief.content}' is justified with confidence {level_result.coherence:.2f}"

        meta_belief = Belief(
            content=meta_content,
            belief_type=BeliefType.META,
            confidence=level_result.coherence,
            justification=[base_belief],
            context=base_belief.context,
            meta_level=next_level,
        )

        return meta_belief

    async def _resolve_contradiction(self, contradiction: Contradiction) -> Resolution:
        """
        Resolve contradição aplicando estratégia sugerida.

        Args:
            contradiction: Contradição a resolver

        Returns:
            Resolution aplicada
        """
        outcome = await self.belief_revision.revise_belief_graph(self.belief_graph, contradiction)
        return outcome.resolution

    def _calculate_coherence(self, levels: List[ReasoningLevel]) -> float:
        """
        Calcula coerência global através de todos os níveis.

        Heurística:
        - Coherence = média de coerências de cada nível
        - Com penalidade se coerência cai entre níveis
        """
        if not levels:
            return 0.0

        # Média das coerências
        avg_coherence = sum(level.coherence for level in levels) / len(levels)

        # Penalidade se coerência degradou entre níveis
        degradation_penalty = 0.0
        for i in range(1, len(levels)):
            drop = levels[i - 1].coherence - levels[i].coherence
            if drop > 0:
                degradation_penalty += drop * 0.1  # 10% penalidade por drop

        return max(0.0, avg_coherence - degradation_penalty)
