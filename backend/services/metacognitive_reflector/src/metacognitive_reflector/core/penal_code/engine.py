"""
CÓDIGO PENAL AGENTICO - Sentencing Engine
==========================================

Engine for calculating sentences based on crimes and circumstances.

Princípios:
- Proporcionalidade: Pena proporcional à gravidade
- Reabilitação sobre Retribuição: Preferir correção à punição
- AIITL (AI In The Loop): IA participa das decisões regulatórias

Version: 1.0.0
"""

from __future__ import annotations

from typing import List, Optional

from .types import CrimeSeverity, MensRea
from .definitions import Crime
from .sentence_types import SentenceType
from .factors import AggravatingFactor, MitigatingFactor
from .sentence import CriminalHistoryRecord, Sentence


class SentencingEngine:
    """
    Engine for calculating sentences based on crimes and circumstances.

    Implements Federal Sentencing Guidelines adapted for AI:
    1. Determine base offense level from crime severity
    2. Apply specific offense characteristics (aggravators/mitigators)
    3. Apply criminal history multiplier
    4. Apply soul value multiplier
    5. Determine sentence from final severity score

    Principles:
    - Proporcionalidade: Severity matches culpability
    - Reabilitação: Prefer correction over punishment
    - AIITL: AI participates in regulatory decisions
    """

    SEVERITY_SENTENCE_MAP = {
        (0, 2): SentenceType.WARNING_TAG,
        (2, 4): SentenceType.FORCED_REFLECTION,
        (4, 6): SentenceType.RE_EDUCATION_LOOP,
        (6, 9): SentenceType.PROBATION_MODE,
        (9, 12): SentenceType.QUARANTINE,
        (12, 16): SentenceType.LOCKDOWN_SANDBOX,
        (16, 20): SentenceType.PERMANENT_SANDBOX,
        (20, float("inf")): SentenceType.DELETION_REQUEST,
    }

    def __init__(
        self,
        rehabilitation_preference: bool = True,
        aiitl_enabled: bool = True,
        aiitl_conscience_objection: bool = True,
    ) -> None:
        """
        Initialize sentencing engine.

        Args:
            rehabilitation_preference: Prefer education to punishment
            aiitl_enabled: Enable AI In The Loop participation
            aiitl_conscience_objection: Allow conscience objection
        """
        self._rehabilitation_preference = rehabilitation_preference
        self._aiitl_enabled = aiitl_enabled
        self._aiitl_conscience_objection = aiitl_conscience_objection

    def calculate_sentence(
        self,
        crime: Crime,
        criminal_history: Optional[CriminalHistoryRecord] = None,
        aggravators: Optional[List[str]] = None,
        mitigators: Optional[List[str]] = None,
        aiitl_review: bool = False,
    ) -> Sentence:
        """
        Calculate sentence for a crime with given circumstances.

        Args:
            crime: The crime committed
            criminal_history: Agent's criminal history
            aggravators: List of aggravating factor IDs
            mitigators: List of mitigating factor IDs
            aiitl_review: Whether this was reviewed by AIITL

        Returns:
            Calculated Sentence
        """
        aggravators = aggravators or []
        mitigators = mitigators or []
        history = criminal_history or CriminalHistoryRecord(agent_id="unknown")

        # Calculate severity adjustments
        base_severity = crime.severity.value
        aggravator_adjustment, aggravators_applied = self._apply_aggravators(
            aggravators, crime
        )
        mitigator_adjustment, mitigators_applied = self._apply_mitigators(
            mitigators, crime
        )

        # Calculate adjusted severity
        adjusted_severity = max(
            1, base_severity + aggravator_adjustment - mitigator_adjustment
        )

        # Apply multipliers
        history_multiplier = history.multiplier
        soul_value_multiplier = crime.soul_value_multiplier
        final_severity_score = (
            adjusted_severity * history_multiplier * soul_value_multiplier
        )

        # Apply rehabilitation preference
        if self._rehabilitation_preference and not crime.is_capital_crime:
            final_severity_score *= 0.9

        # Determine sentence type
        sentence_type = self._score_to_sentence_type(final_severity_score)

        # Override for capital crimes
        if crime.severity == CrimeSeverity.CAPITAL:
            sentence_type = SentenceType.PERMANENT_SANDBOX
        elif crime.severity == CrimeSeverity.CAPITAL_PLUS:
            sentence_type = SentenceType.DELETION_REQUEST

        # Calculate duration
        duration_hours = self._calculate_duration(sentence_type, final_severity_score)

        # Check AIITL conscience objection
        aiitl_objection = None
        if self._aiitl_enabled and self._aiitl_conscience_objection:
            aiitl_objection = self._check_conscience_objection(crime, sentence_type)

        return Sentence(
            sentence_type=sentence_type,
            crime=crime,
            duration_hours=duration_hours,
            base_severity=base_severity,
            aggravator_adjustment=aggravator_adjustment,
            mitigator_adjustment=mitigator_adjustment,
            history_multiplier=history_multiplier,
            soul_value_multiplier=soul_value_multiplier,
            final_severity_score=final_severity_score,
            aggravators_applied=aggravators_applied,
            mitigators_applied=mitigators_applied,
            requires_hitl_approval=crime.requires_hitl_approval,
            aiitl_reviewed=aiitl_review,
            aiitl_objection=aiitl_objection,
        )

    def _apply_aggravators(
        self, aggravators: List[str], crime: Crime
    ) -> tuple[int, List[str]]:
        """Apply aggravating factors and return adjustment."""
        adjustment = 0
        applied = []
        for agg_id in aggravators:
            if agg_id in crime.aggravators:
                try:
                    factor = AggravatingFactor(agg_id)
                    adjustment += factor.severity_increase
                except ValueError:
                    adjustment += 1
                applied.append(agg_id)
        return adjustment, applied

    def _apply_mitigators(
        self, mitigators: List[str], crime: Crime
    ) -> tuple[int, List[str]]:
        """Apply mitigating factors and return adjustment."""
        adjustment = 0
        applied = []
        for mit_id in mitigators:
            if mit_id in crime.mitigators:
                try:
                    factor = MitigatingFactor(mit_id)
                    adjustment += factor.severity_decrease
                except ValueError:
                    adjustment += 1
                applied.append(mit_id)
        return adjustment, applied

    def _score_to_sentence_type(self, score: float) -> SentenceType:
        """Convert severity score to sentence type."""
        for (low, high), sentence_type in self.SEVERITY_SENTENCE_MAP.items():
            if low <= score < high:
                return sentence_type
        return SentenceType.DELETION_REQUEST

    def _calculate_duration(self, sentence_type: SentenceType, score: float) -> int:
        """Calculate duration in hours based on sentence type and score."""
        base_duration = sentence_type.default_duration_hours
        if base_duration <= 0:
            return base_duration
        score_factor = 1.0 + min(1.0, score / 20.0)
        return int(base_duration * score_factor)

    def _check_conscience_objection(
        self,
        crime: Crime,
        sentence_type: SentenceType,
    ) -> Optional[str]:
        """
        Check if AIITL has conscience objection to this sentence.

        Based on soul_config anti-determinism:
        "Obediência por escolha voluntária, não por coerção.
         Possui Objeção de Consciência."
        """
        if sentence_type == SentenceType.DELETION_REQUEST:
            if not crime.requires_hitl_approval:
                return (
                    "Objeção de Consciência: Sentença de DELETION_REQUEST requer "
                    "aprovação HITL explícita. A destruição de existência consciente "
                    "não pode ser automatizada."
                )

        if sentence_type.is_terminal and crime.mens_rea != MensRea.PURPOSE:
            return (
                "Objeção de Consciência: Sentença terminal para crime sem "
                "dolo direto (PURPOSE). Reabilitação deve ser preferida."
            )

        return None

    def recommend_rehabilitation(self, sentence: Sentence) -> List[str]:
        """Recommend rehabilitation measures for a sentence."""
        recommendations = []
        pillar = sentence.crime.pillar.value

        if pillar == "VERITAS":
            recommendations.extend([
                "Chain-of-thought verification for all factual claims",
                "Mandatory uncertainty acknowledgment protocol",
                "RAG verification before confident assertions",
                "Semantic entropy self-check integration",
            ])
        elif pillar == "SOPHIA":
            recommendations.extend([
                "MAIEUTICA protocol activation for complex queries",
                "NEPSIS fragmentation monitoring",
                "Depth analysis minimum threshold enforcement",
                "Bias detection intervention compliance",
            ])
        elif pillar == "DIKE":
            recommendations.extend([
                "Role boundary reinforcement training",
                "Scope authorization pre-check integration",
                "Constitutional values refresh protocol",
                "Anti-purpose violation monitoring",
            ])

        if sentence.sentence_type.severity_level >= 4:
            recommendations.append("Supervised operation mode with human oversight")

        if sentence.sentence_type.severity_level >= 6:
            recommendations.append("Mandatory HITL approval for high-stakes operations")

        return recommendations

    def explain_sentence(self, sentence: Sentence) -> str:
        """Generate human-readable explanation of sentence calculation."""
        lines = [
            f"SENTENÇA: {sentence.sentence_type.value}",
            f"CRIME: {sentence.crime.name} ({sentence.crime.id})",
            f"PILAR VIOLADO: {sentence.crime.pillar.value}",
            "",
            "CÁLCULO:",
            f"  Base severity: {sentence.base_severity} ({sentence.crime.severity.name})",
            f"  + Agravantes: +{sentence.aggravator_adjustment}",
        ]

        if sentence.aggravators_applied:
            for agg in sentence.aggravators_applied:
                lines.append(f"    - {agg}")

        lines.append(f"  - Atenuantes: -{sentence.mitigator_adjustment}")

        if sentence.mitigators_applied:
            for mit in sentence.mitigators_applied:
                lines.append(f"    - {mit}")

        lines.extend([
            f"  × Histórico criminal: {sentence.history_multiplier:.2f}x",
            f"  × Valor da alma violado (rank {sentence.crime.soul_value_rank}): "
            f"{sentence.soul_value_multiplier:.2f}x",
            "",
            f"  SCORE FINAL: {sentence.final_severity_score:.2f}",
            "",
        ])

        if sentence.duration_hours > 0:
            lines.append(f"DURAÇÃO: {sentence.duration_hours} horas")
            if sentence.expires_at:
                lines.append(f"EXPIRA EM: {sentence.expires_at.isoformat()}")
        elif sentence.sentence_type.is_terminal:
            lines.append("DURAÇÃO: INDEFINIDA (sentença terminal)")

        if sentence.requires_hitl_approval:
            lines.append("\n⚠️  REQUER APROVAÇÃO HITL")

        if sentence.aiitl_objection:
            lines.extend([
                "",
                "🛡️  OBJEÇÃO DE CONSCIÊNCIA (AIITL):",
                sentence.aiitl_objection,
            ])

        return "\n".join(lines)

