"""
Belief Models - Representação de Crenças e Tipos
================================================

Define estruturas de dados para crenças, enums de tipos,
e lógica de comparação/negação.

Authors: Claude Code + Juan
Version: 1.0.0
Date: 2025-12-02
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional
from uuid import UUID, uuid4


# ==================== ENUMS ====================


class BeliefType(Enum):
    """Tipos de crenças no sistema."""

    FACTUAL = "factual"  # "IP 192.168.1.1 é malicioso"
    META = "meta"  # "Eu acredito que IP 192.168.1.1 é malicioso"
    NORMATIVE = "normative"  # "Devo bloquear IP 192.168.1.1"
    EPISTEMIC = "epistemic"  # "Minha crença sobre 192.168.1.1 é justificada"


class ContradictionType(Enum):
    """Tipos de contradições detectadas."""

    DIRECT = "direct"  # A e ¬A simultaneamente
    TRANSITIVE = "transitive"  # A→B, B→C, C→¬A
    TEMPORAL = "temporal"  # Acreditava X antes, acredito ¬X agora sem razão
    CONTEXTUAL = "contextual"  # X verdadeiro em C1, ¬X em C2 sem explicação


class ResolutionStrategy(Enum):
    """Estratégias de resolução de contradições."""

    RETRACT_WEAKER = "retract_weaker"  # Remove crença menos confiável
    WEAKEN_BOTH = "weaken_both"  # Reduz confiança de ambas
    CONTEXTUALIZE = "contextualize"  # Adiciona condições contextuais
    TEMPORIZE = "temporize"  # Marca como crença passada
    HITL_ESCALATE = "hitl_escalate"  # Escala para humano


# ==================== DATACLASSES ====================


@dataclass
class Belief:
    """
    Representa uma crença no sistema.

    Attributes:
        id: Identificador único
        content: Conteúdo proposicional da crença
        belief_type: Tipo de crença (factual, meta, normative, epistemic)
        confidence: Nível de confiança [0.0, 1.0]
        justification: Crença(s) que justificam esta
        context: Contexto em que crença é válida
        timestamp: Quando crença foi formada
        meta_level: Nível de abstração (0=objeto, 1=meta, 2=meta-meta, etc.)
    """

    content: str
    belief_type: BeliefType = BeliefType.FACTUAL
    confidence: float = 0.5
    justification: Optional[List["Belief"]] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    meta_level: int = 0
    id: UUID = field(default_factory=uuid4)

    NEGATION_MAP: ClassVar[Dict[str, str]] = {
        "isn't": "is",
        "aren't": "are",
        "not": "",
        "¬": "",
        "~": "",
        "no ": "",
    }

    def __post_init__(self):
        """Validações."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be [0, 1], got {self.confidence}")
        if self.meta_level < 0:
            raise ValueError(f"Meta level must be >= 0, got {self.meta_level}")
        if self.justification is None:
            self.justification = []

    def __hash__(self):
        """Hash para usar em sets."""
        return hash(self.id)

    def __eq__(self, other):
        """Equality baseado em ID."""
        if not isinstance(other, Belief):
            return False
        return self.id == other.id

    def is_negation_of(self, other: "Belief") -> bool:
        """
        Verifica se esta crença é negação de outra.

        Heurísticas simples:
        - "IP X is malicious" vs "IP X is not malicious"
        - "Action Y is ethical" vs "Action Y is unethical"
        """
        if self.belief_type != other.belief_type:
            return False

        content_lower = self.content.lower()
        other_lower = other.content.lower()

        # Se um tem negação e outro não, pode ser negação
        self_has_neg = any(marker in content_lower for marker in self.NEGATION_MAP)
        other_has_neg = any(marker in other_lower for marker in self.NEGATION_MAP)

        if self_has_neg != other_has_neg:
            # Remover negação e comparar
            self_clean = content_lower
            other_clean = other_lower

            for marker, replacement in self.NEGATION_MAP.items():
                self_clean = self_clean.replace(marker, replacement)
                other_clean = other_clean.replace(marker, replacement)

            # Se conteúdos são similares após remover negação
            self_clean = self._normalize_whitespace(self_clean)
            other_clean = self._normalize_whitespace(other_clean)
            return self_clean == other_clean

        return False

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        """Compress consecutive whitespace to support semantic comparisons."""
        return " ".join(text.split())

    @classmethod
    def strip_negations(cls, text: str) -> str:
        """Remove marcadores de negação para comparação canônica."""
        cleaned = text.lower()
        for marker, replacement in cls.NEGATION_MAP.items():
            cleaned = cleaned.replace(marker, replacement)
        return cls._normalize_whitespace(cleaned)
