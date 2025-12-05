"""
Contradiction Models - Contradições e Resoluções
================================================

Define estruturas de dados para contradições detectadas
e resoluções aplicadas.

Authors: Claude Code + Juan
Version: 1.0.0
Date: 2025-12-02
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from .belief_models import Belief, ContradictionType, ResolutionStrategy


@dataclass
class Contradiction:
    """
    Representa uma contradição detectada.

    Attributes:
        belief_a: Primeira crença contraditória
        belief_b: Segunda crença contraditória
        contradiction_type: Tipo de contradição
        severity: Severidade [0.0, 1.0]
        explanation: Explicação da contradição
        suggested_resolution: Estratégia sugerida
    """

    belief_a: Belief
    belief_b: Belief
    contradiction_type: ContradictionType
    severity: float = 1.0
    explanation: str = ""
    suggested_resolution: ResolutionStrategy = ResolutionStrategy.RETRACT_WEAKER
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self):
        """Gerar explicação se não fornecida."""
        if not self.explanation:
            self.explanation = (
                f"Contradiction detected: '{self.belief_a.content}' "
                f"contradicts '{self.belief_b.content}' "
                f"(type: {self.contradiction_type.value})"
            )


@dataclass
class Resolution:
    """
    Representa a resolução de uma contradição.

    Attributes:
        contradiction: Contradição resolvida
        strategy: Estratégia usada
        beliefs_modified: Crenças modificadas
        beliefs_removed: Crenças removidas
        new_beliefs: Novas crenças adicionadas
        timestamp: Quando resolução foi aplicada
    """

    contradiction: Contradiction
    strategy: ResolutionStrategy
    beliefs_modified: List[Belief] = field(default_factory=list)
    beliefs_removed: List[Belief] = field(default_factory=list)
    new_beliefs: List[Belief] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    id: UUID = field(default_factory=uuid4)
