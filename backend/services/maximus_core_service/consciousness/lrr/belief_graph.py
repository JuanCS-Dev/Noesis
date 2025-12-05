"""
Belief Graph - Grafo de Crenças e Detecção de Contradições
===========================================================

Implementa estrutura de dados para armazenar crenças e suas
inter-relações, incluindo detecção de contradições.

Authors: Claude Code + Juan
Version: 1.0.0
Date: 2025-12-02
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Set
from uuid import UUID

from .belief_models import Belief, ResolutionStrategy
from .contradiction_models import Contradiction, ContradictionType, Resolution

logger = logging.getLogger(__name__)


class BeliefGraph:
    """
    Grafo de crenças e suas inter-relações.

    Permite:
    - Adicionar crenças e justificações
    - Detectar contradições (diretas, transitivas, temporais)
    - Resolver contradições através de revisão
    - Calcular coerência do grafo
    """

    def __init__(self):
        """Initialize belief graph."""
        self.beliefs: Set[Belief] = set()
        self.justifications: Dict[UUID, List[Belief]] = defaultdict(list)
        self.timestamp_index: Dict[datetime, Set[Belief]] = defaultdict(set)
        self.context_index: Dict[str, Set[Belief]] = defaultdict(set)

    def add_belief(self, belief: Belief, justification: Optional[List[Belief]] = None) -> None:
        """
        Adiciona crença ao grafo.

        Args:
            belief: Crença a adicionar
            justification: Crenças que justificam esta
        """
        self.beliefs.add(belief)

        if justification:
            self.justifications[belief.id].extend(justification)
            belief.justification = justification

        # Indexar por timestamp
        self.timestamp_index[belief.timestamp].add(belief)

        # Indexar por contexto
        for key in belief.context:
            self.context_index[key].add(belief)

    def detect_contradictions(self) -> List[Contradiction]:
        """
        Detecta todas as contradições no grafo.

        Returns:
            Lista de contradições ordenadas por severidade
        """
        contradictions: List[Contradiction] = []

        # Contradições diretas (A e ¬A)
        contradictions.extend(self._detect_direct_contradictions())

        # Contradições transitivas (A→B, B→C, C→¬A)
        contradictions.extend(self._detect_transitive_contradictions())

        # Contradições temporais
        contradictions.extend(self._detect_temporal_contradictions())

        # Contradições contextuais
        contradictions.extend(self._detect_contextual_contradictions())

        # Ordenar por severidade
        return sorted(contradictions, key=lambda c: c.severity, reverse=True)

    def _detect_direct_contradictions(self) -> List[Contradiction]:
        """Detecta contradições diretas (A e ¬A)."""
        contradictions = []

        beliefs_list = list(self.beliefs)
        for i, belief_a in enumerate(beliefs_list):
            for belief_b in beliefs_list[i + 1 :]:
                if belief_a.is_negation_of(belief_b):
                    # Severity baseado em confiança
                    severity = min(belief_a.confidence, belief_b.confidence)

                    # Sugerir estratégia
                    if belief_a.confidence > belief_b.confidence:
                        strategy = ResolutionStrategy.RETRACT_WEAKER
                    elif abs(belief_a.confidence - belief_b.confidence) < 0.1:
                        strategy = ResolutionStrategy.WEAKEN_BOTH
                    else:
                        strategy = ResolutionStrategy.RETRACT_WEAKER

                    contradictions.append(
                        Contradiction(
                            belief_a=belief_a,
                            belief_b=belief_b,
                            contradiction_type=ContradictionType.DIRECT,
                            severity=severity,
                            suggested_resolution=strategy,
                        )
                    )

        return contradictions

    def _detect_transitive_contradictions(self) -> List[Contradiction]:
        """
        Detecta contradições transitivas (A→B, B→C, C→¬A).

        Usa BFS para encontrar caminhos de justificação que levam
        a contradições indiretas.
        """
        contradictions = []

        # Para cada crença, seguir cadeia de justificações
        for belief in self.beliefs:
            # BFS para encontrar caminhos de justificação
            visited = set()
            queue = [(belief, [belief])]

            while queue:
                current, path = queue.pop(0)

                if (
                    current.id in visited
                ):  # pragma: no cover - BFS deduplication for diamond patterns in justification graphs
                    continue
                visited.add(current.id)

                # Para cada justificação desta crença
                for justification in self.justifications.get(current.id, []):
                    new_path = path + [justification]

                    # Se encontramos negação da crença original
                    if justification.is_negation_of(belief):
                        # Temos contradição transitiva!
                        contradictions.append(
                            Contradiction(
                                belief_a=belief,
                                belief_b=justification,
                                contradiction_type=ContradictionType.TRANSITIVE,
                                severity=0.6,  # Menos severa que direta
                                suggested_resolution=ResolutionStrategy.WEAKEN_BOTH,
                                explanation=f"Transitive contradiction: {' → '.join(b.content[:30] for b in new_path)}",
                            )
                        )
                    else:
                        # Continuar BFS
                        if len(new_path) < 5:  # Limitar profundidade
                            queue.append((justification, new_path))

        return contradictions

    def _detect_temporal_contradictions(self) -> List[Contradiction]:
        """Detecta contradições temporais."""
        contradictions = []

        # Agrupar crenças por conteúdo similar (ignorando marcadores de negação)
        content_groups: Dict[str, List[Belief]] = defaultdict(list)
        for belief in self.beliefs:
            key = Belief.strip_negations(belief.content)
            content_groups[key].append(belief)

        # Detectar mudanças sem justificação
        for beliefs in content_groups.values():
            if len(beliefs) < 2:
                continue

            # Ordenar por timestamp
            sorted_beliefs = sorted(beliefs, key=lambda b: b.timestamp)

            for i in range(len(sorted_beliefs) - 1):
                current = sorted_beliefs[i]
                next_belief = sorted_beliefs[i + 1]

                # Se são negações e não há justificação
                if current.is_negation_of(next_belief) and not next_belief.justification:
                    contradictions.append(
                        Contradiction(
                            belief_a=current,
                            belief_b=next_belief,
                            contradiction_type=ContradictionType.TEMPORAL,
                            severity=0.7,
                            suggested_resolution=ResolutionStrategy.TEMPORIZE,
                            explanation=f"Belief changed from '{current.content}' to '{next_belief.content}' without justification",
                        )
                    )

        return contradictions

    def _detect_contextual_contradictions(self) -> List[Contradiction]:
        """
        Detecta contradições contextuais.

        Identifica crenças que são contraditórias em contextos diferentes
        sem explicação adequada.
        """
        contradictions = []

        # Agrupar crenças por chaves de contexto compartilhadas
        for key, beliefs_with_context in self.context_index.items():
            if len(beliefs_with_context) < 2:
                continue

            beliefs_list = list(beliefs_with_context)
            for i, belief_a in enumerate(beliefs_list):
                for belief_b in beliefs_list[i + 1 :]:
                    # Se são negações mas compartilham contexto
                    if belief_a.is_negation_of(belief_b):
                        # Verificar se contextos são realmente diferentes
                        context_diff = set(belief_a.context.keys()) ^ set(belief_b.context.keys())

                        if context_diff:
                            contradictions.append(
                                Contradiction(
                                    belief_a=belief_a,
                                    belief_b=belief_b,
                                    contradiction_type=ContradictionType.CONTEXTUAL,
                                    severity=0.5,
                                    suggested_resolution=ResolutionStrategy.CONTEXTUALIZE,
                                    explanation=f"Contextual contradiction in context '{key}': differing contexts {context_diff}",
                                )
                            )

        return contradictions

    def resolve_belief(self, belief: Belief, resolution: Resolution) -> None:
        """
        Resolve contradição aplicando resolução.

        Args:
            belief: Crença envolvida na contradição
            resolution: Resolução a aplicar
        """
        if resolution.strategy == ResolutionStrategy.RETRACT_WEAKER:
            # Remover crença mais fraca
            if belief in self.beliefs:
                self.beliefs.remove(belief)
                logger.info(f"Retracted belief: {belief.content}")

        elif resolution.strategy == ResolutionStrategy.WEAKEN_BOTH:
            # Reduzir confiança (criar nova crença com confiança menor)
            new_belief = Belief(
                content=belief.content,
                belief_type=belief.belief_type,
                confidence=belief.confidence * 0.5,
                justification=belief.justification,
                context=belief.context,
                meta_level=belief.meta_level,
            )
            if belief in self.beliefs:
                self.beliefs.remove(belief)
            self.beliefs.add(new_belief)
            logger.info(
                f"Weakened belief: {belief.content} (conf: {belief.confidence} → {new_belief.confidence})"
            )

        elif resolution.strategy == ResolutionStrategy.TEMPORIZE:
            # Marcar como crença passada (adicionar ao contexto)
            belief.context["temporal_status"] = "past"
            belief.context["superseded_at"] = datetime.now().isoformat()
            logger.info(f"Temporized belief: {belief.content}")

        elif resolution.strategy == ResolutionStrategy.CONTEXTUALIZE:
            # Adicionar contexto que explica aparente contradição
            belief.context["contextualized"] = True
            belief.context["context_note"] = "Valid in specific context only"
            logger.info(f"Contextualized belief: {belief.content}")

        elif resolution.strategy == ResolutionStrategy.HITL_ESCALATE:
            # Marcar para escalação humana
            belief.context["hitl_review_required"] = True
            belief.context["escalated_at"] = datetime.now().isoformat()
            logger.warning(f"Escalated belief to HITL: {belief.content}")

    def calculate_coherence(self) -> float:
        """
        Calcula coerência do grafo.

        Heurística:
        - Coherence = 1.0 - (contradictions / total_pairs)
        - Com penalidade por contradições de alta severidade

        Returns:
            Coherence score [0.0, 1.0]
        """
        if len(self.beliefs) < 2:
            return 1.0

        contradictions = self.detect_contradictions()
        if not contradictions:
            return 1.0

        # Total de pares possíveis
        n = len(self.beliefs)
        total_pairs = n * (n - 1) / 2

        # Penalidade por contradições (ponderada por severidade)
        penalty = sum(c.severity for c in contradictions) / total_pairs

        return max(0.0, 1.0 - penalty)
