"""
Reasoning Models - Estruturas de Raciocínio Recursivo
=====================================================

Define estruturas de dados para passos de raciocínio,
níveis de abstração, e resultados completos.

Authors: Claude Code + Juan
Version: 1.0.0
Date: 2025-12-02
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from .belief_models import Belief
from .contradiction_models import Contradiction, Resolution

if TYPE_CHECKING:  # pragma: no cover
    from consciousness.mea.attention_schema import AttentionState
    from consciousness.mea.boundary_detector import BoundaryAssessment
    from consciousness.mea.self_model import IntrospectiveSummary
    from consciousness.episodic_memory import Episode
    from .introspection_engine import IntrospectionReport
    from .meta_monitor import MetaMonitoringReport


@dataclass
class ReasoningStep:
    """
    Representa um passo de raciocínio.

    Attributes:
        belief: Crença sendo processada
        meta_level: Nível de abstração
        justification_chain: Cadeia de justificações
        confidence_assessment: Avaliação de confiança
        timestamp: Quando passo foi executado
    """

    belief: Belief
    meta_level: int
    justification_chain: List[Belief] = field(default_factory=list)
    confidence_assessment: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ReasoningLevel:
    """
    Representa um nível completo de raciocínio.

    Attributes:
        level: Número do nível (0=objeto, 1=meta, etc.)
        beliefs: Crenças neste nível
        coherence: Coerência interna [0.0, 1.0]
        steps: Passos de raciocínio executados
    """

    level: int
    beliefs: List[Belief] = field(default_factory=list)
    coherence: float = 1.0
    steps: List[ReasoningStep] = field(default_factory=list)


@dataclass
class RecursiveReasoningResult:
    """
    Resultado de raciocínio recursivo completo.

    Attributes:
        levels: Níveis de raciocínio executados
        final_depth: Profundidade alcançada
        coherence_score: Coerência global [0.0, 1.0]
        contradictions_detected: Contradições encontradas
        resolutions_applied: Resoluções aplicadas
        timestamp: Quando raciocínio foi executado
    """

    levels: List[ReasoningLevel]
    final_depth: int
    coherence_score: float
    contradictions_detected: List[Contradiction] = field(default_factory=list)
    resolutions_applied: List[Resolution] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0
    meta_report: Optional["MetaMonitoringReport"] = None
    introspection_report: Optional["IntrospectionReport"] = None
    attention_state: Optional["AttentionState"] = None
    boundary_assessment: Optional["BoundaryAssessment"] = None
    self_summary: Optional["IntrospectiveSummary"] = None
    episodic_episode: Optional["Episode"] = None
    episodic_narrative: Optional[str] = None
    episodic_coherence: Optional[float] = None
