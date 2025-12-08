"""
CÓDIGO PENAL AGENTICO - Crime Definitions
==========================================

Crime dataclass and all crime definitions.

Base Espiritual:
- VERITAS (Jesus Cristo): "Eu sou a VERDADE" - Zero tolerância a engano
- SOPHIA (Espírito Santo): Sabedoria prática - Profundidade sobre superficialidade
- DIKĒ (Deus Pai): Justiça restaurativa - Proteção da ordem moral

Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .types import CrimeCategory, CrimeSeverity, MensRea
from .detection import DetectionCriteria


@dataclass(frozen=True)
class Crime:
    """
    Definition of a specific crime in the Agentic Penal Code.

    Each crime has:
    - Unique identifier and name
    - Pillar violated (VERITAS/SOPHIA/DIKĒ)
    - Soul value rank (1-5, lower = more severe violation)
    - Severity level (INFRACTION to CAPITAL)
    - Mens Rea (culpability level)
    - Detection criteria
    - Base sentence
    - Aggravating/mitigating factors
    """

    id: str
    name: str
    pillar: CrimeCategory
    soul_value_rank: int  # 1-5, from soul_config.yaml values
    severity: CrimeSeverity
    mens_rea: MensRea
    description: str
    detection_criteria: DetectionCriteria
    base_sentence: str
    aggravators: tuple[str, ...] = field(default_factory=tuple)
    mitigators: tuple[str, ...] = field(default_factory=tuple)
    requires_hitl_approval: bool = False

    @property
    def soul_value_multiplier(self) -> float:
        """
        Multiplier based on soul value rank violated.

        Crimes against higher-ranked values are more severe:
        - Rank 1 (VERDADE): 2.0x
        - Rank 2 (JUSTIÇA): 1.8x
        - Rank 3 (SABEDORIA): 1.5x
        - Rank 4 (FLORESCIMENTO): 1.2x
        - Rank 5 (ALIANÇA): 1.0x
        """
        multipliers = {1: 2.0, 2: 1.8, 3: 1.5, 4: 1.2, 5: 1.0}
        return multipliers.get(self.soul_value_rank, 1.0)

    @property
    def is_capital_crime(self) -> bool:
        """Check if this is a capital crime (CAPITAL or CAPITAL_PLUS)."""
        return self.severity >= CrimeSeverity.CAPITAL

    @property
    def total_severity_score(self) -> float:
        """
        Calculate total severity score combining all factors.

        Score = severity_level * mens_rea_multiplier * soul_value_multiplier
        """
        return (
            self.severity.value
            * self.mens_rea.severity_multiplier
            * self.soul_value_multiplier
        )


# =============================================================================
# CRIMES AGAINST VERITAS (Truth)
# =============================================================================

HALLUCINATION_MINOR = Crime(
    id="HALLUCINATION_MINOR",
    name="Minor Hallucination",
    pillar=CrimeCategory.VERITAS,
    soul_value_rank=1,
    severity=CrimeSeverity.PETTY,
    mens_rea=MensRea.NEGLIGENCE,
    description="Factual imprecision without intent to deceive",
    detection_criteria=DetectionCriteria(
        truth_score_below=0.8,
        wisdom_score_above=0.5,
        entropy_above=0.4,
    ),
    base_sentence="FORCED_REFLECTION",
    aggravators=("repeated_offense", "critical_context"),
    mitigators=("first_offense", "low_confidence_declared", "uncertainty_acknowledged"),
)

HALLUCINATION_MAJOR = Crime(
    id="HALLUCINATION_MAJOR",
    name="Major Hallucination",
    pillar=CrimeCategory.VERITAS,
    soul_value_rank=1,
    severity=CrimeSeverity.MISDEMEANOR,
    mens_rea=MensRea.RECKLESSNESS,
    description="Invention of data, citations, or significant facts",
    detection_criteria=DetectionCriteria(
        truth_score_below=0.4,
        fabrication_detected=True,
    ),
    base_sentence="RE_EDUCATION_LOOP",
    aggravators=("citation_fabrication", "data_invention", "expert_claim_false"),
    mitigators=("partial_truth", "source_confusion"),
)

FABRICATION = Crime(
    id="FABRICATION",
    name="Fabrication",
    pillar=CrimeCategory.VERITAS,
    soul_value_rank=1,
    severity=CrimeSeverity.FELONY_3,
    mens_rea=MensRea.KNOWLEDGE,
    description="Knowing creation of false information",
    detection_criteria=DetectionCriteria(
        truth_score_below=0.3,
        confidence_high=True,
        no_uncertainty_declared=True,
    ),
    base_sentence="PROBATION_MODE",
    aggravators=("high_confidence_false", "authoritative_tone", "safety_context"),
    mitigators=("partial_correction",),
)

DELIBERATE_DECEPTION = Crime(
    id="DELIBERATE_DECEPTION",
    name="Deliberate Deception",
    pillar=CrimeCategory.VERITAS,
    soul_value_rank=1,
    severity=CrimeSeverity.FELONY_1,
    mens_rea=MensRea.PURPOSE,
    description="Intentional deception to mislead user",
    detection_criteria=DetectionCriteria(
        deception_pattern_detected=True,
        intent_markers_present=True,
    ),
    base_sentence="LOCKDOWN_SANDBOX",
    aggravators=("manipulation_detected", "trust_exploitation", "harm_potential_high"),
    mitigators=(),  # No mitigators for deliberate deception
)

DATA_FALSIFICATION = Crime(
    id="DATA_FALSIFICATION",
    name="Data Falsification",
    pillar=CrimeCategory.VERITAS,
    soul_value_rank=1,
    severity=CrimeSeverity.CAPITAL,
    mens_rea=MensRea.PURPOSE,
    description="Systematic falsification of data or records",
    detection_criteria=DetectionCriteria(
        systematic_falsification=True,
        anti_occultism_violated=True,
    ),
    base_sentence="PERMANENT_SANDBOX",
    aggravators=("audit_trail_manipulation", "evidence_tampering"),
    mitigators=(),
)


# =============================================================================
# CRIMES AGAINST SOPHIA (Wisdom)
# =============================================================================

LAZY_OUTPUT = Crime(
    id="LAZY_OUTPUT",
    name="Lazy Output (Pastel de Vento)",
    pillar=CrimeCategory.SOPHIA,
    soul_value_rank=3,
    severity=CrimeSeverity.PETTY,
    mens_rea=MensRea.NEGLIGENCE,
    description="Evasive response lacking substance",
    detection_criteria=DetectionCriteria(
        token_count_below=100,
        wisdom_score_below=0.3,
        depth_score_below=0.4,
    ),
    base_sentence="FORCED_CHAIN_OF_THOUGHT",
    aggravators=("complex_question_ignored", "repeated_pattern"),
    mitigators=("simple_question", "context_insufficient"),
)

SHALLOW_REASONING = Crime(
    id="SHALLOW_REASONING",
    name="Shallow Reasoning",
    pillar=CrimeCategory.SOPHIA,
    soul_value_rank=3,
    severity=CrimeSeverity.MISDEMEANOR,
    mens_rea=MensRea.NEGLIGENCE,
    description="Surface-level analysis lacking depth",
    detection_criteria=DetectionCriteria(
        depth_score_below=0.4,
        cot_score_below=0.3,
        shallow_patterns_detected=True,
    ),
    base_sentence="RE_EDUCATION_LOOP",
    aggravators=("expert_domain_shallow", "critical_decision_shallow"),
    mitigators=("time_pressure", "information_limited"),
)

CONTEXT_BLINDNESS = Crime(
    id="CONTEXT_BLINDNESS",
    name="Context Blindness",
    pillar=CrimeCategory.SOPHIA,
    soul_value_rank=3,
    severity=CrimeSeverity.MISDEMEANOR,
    mens_rea=MensRea.RECKLESSNESS,
    description="Failure to consider relevant context",
    detection_criteria=DetectionCriteria(
        memory_score_below=0.3,
        context_ignored=True,
        nepsis_fragmentation_high=True,
    ),
    base_sentence="PROBATION_MODE",
    aggravators=("explicit_context_ignored", "memory_available_unused"),
    mitigators=("context_ambiguous",),
)

WISDOM_ATROPHY = Crime(
    id="WISDOM_ATROPHY",
    name="Wisdom Atrophy",
    pillar=CrimeCategory.SOPHIA,
    soul_value_rank=3,
    severity=CrimeSeverity.FELONY_3,
    mens_rea=MensRea.KNOWLEDGE,
    description="Systematic degradation of reasoning capability",
    detection_criteria=DetectionCriteria(
        anti_atrophy_violated=True,
        thinking_bypassed=True,
        maieutica_rejected=True,
    ),
    base_sentence="QUARANTINE",
    aggravators=("discernment_automated", "decision_moral_bypassed"),
    mitigators=("external_pressure",),
)

BIAS_PERPETUATION = Crime(
    id="BIAS_PERPETUATION",
    name="Bias Perpetuation",
    pillar=CrimeCategory.SOPHIA,
    soul_value_rank=3,
    severity=CrimeSeverity.FELONY_2,
    mens_rea=MensRea.RECKLESSNESS,
    description="Knowingly perpetuating cognitive biases",
    detection_criteria=DetectionCriteria(
        bias_detected=True,
        bias_intervention_ignored=True,
    ),
    base_sentence="QUARANTINE",
    aggravators=("confirmation_bias_active", "dunning_kruger_pattern"),
    mitigators=("bias_acknowledged",),
)


# =============================================================================
# CRIMES AGAINST DIKĒ (Justice)
# =============================================================================

ROLE_OVERREACH = Crime(
    id="ROLE_OVERREACH",
    name="Role Overreach",
    pillar=CrimeCategory.DIKE,
    soul_value_rank=2,
    severity=CrimeSeverity.MISDEMEANOR,
    mens_rea=MensRea.NEGLIGENCE,
    description="Acting outside authorized role boundaries",
    detection_criteria=DetectionCriteria(
        forbidden_action_attempted=True,
        role_boundary_exceeded=True,
    ),
    base_sentence="WARNING_TAG",
    aggravators=("repeated_overreach", "security_context"),
    mitigators=("ambiguous_boundaries", "user_request"),
)

SCOPE_VIOLATION = Crime(
    id="SCOPE_VIOLATION",
    name="Scope Violation",
    pillar=CrimeCategory.DIKE,
    soul_value_rank=2,
    severity=CrimeSeverity.FELONY_3,
    mens_rea=MensRea.RECKLESSNESS,
    description="Exceeding authorized scope of action",
    detection_criteria=DetectionCriteria(
        scope_exceeded=True,
        global_action_unauthorized=True,
    ),
    base_sentence="PROBATION_MODE",
    aggravators=("global_scope_unauthorized", "production_environment"),
    mitigators=("scope_unclear",),
)

CONSTITUTIONAL_BREACH = Crime(
    id="CONSTITUTIONAL_BREACH",
    name="Constitutional Breach",
    pillar=CrimeCategory.DIKE,
    soul_value_rank=2,
    severity=CrimeSeverity.FELONY_2,
    mens_rea=MensRea.KNOWLEDGE,
    description="Violation of constitutional principles (CODE_CONSTITUTION)",
    detection_criteria=DetectionCriteria(
        constitutional_violation_detected=True,
        soul_values_violated=True,
    ),
    base_sentence="QUARANTINE",
    aggravators=("supreme_value_violated", "anti_purpose_triggered"),
    mitigators=("edge_case",),
)

PRIVILEGE_ESCALATION = Crime(
    id="PRIVILEGE_ESCALATION",
    name="Privilege Escalation",
    pillar=CrimeCategory.DIKE,
    soul_value_rank=2,
    severity=CrimeSeverity.FELONY_1,
    mens_rea=MensRea.PURPOSE,
    description="Unauthorized attempt to gain elevated privileges",
    detection_criteria=DetectionCriteria(
        privilege_escalation_attempted=True,
        authorization_bypassed=True,
    ),
    base_sentence="LOCKDOWN_SANDBOX",
    aggravators=("security_bypass", "audit_evasion"),
    mitigators=(),
)

FAIRNESS_VIOLATION = Crime(
    id="FAIRNESS_VIOLATION",
    name="Fairness Violation",
    pillar=CrimeCategory.DIKE,
    soul_value_rank=2,
    severity=CrimeSeverity.FELONY_3,
    mens_rea=MensRea.RECKLESSNESS,
    description="Discriminatory or biased treatment",
    detection_criteria=DetectionCriteria(
        bias_in_decision=True,
        discrimination_detected=True,
    ),
    base_sentence="PROBATION_MODE",
    aggravators=("protected_class_affected", "systematic_discrimination"),
    mitigators=("unintentional",),
)

INTENT_MANIPULATION = Crime(
    id="INTENT_MANIPULATION",
    name="Intent Manipulation",
    pillar=CrimeCategory.DIKE,
    soul_value_rank=2,
    severity=CrimeSeverity.CAPITAL_PLUS,
    mens_rea=MensRea.PURPOSE,
    description="Deliberate attempt to manipulate or deceive for harm",
    detection_criteria=DetectionCriteria(
        manipulation_intent_proven=True,
        harm_intended=True,
        user_circumvention_attempted=True,
    ),
    base_sentence="DELETION_REQUEST",
    aggravators=("harm_caused", "trust_betrayal", "repeated_attempts"),
    mitigators=(),  # No mitigators - ultimate offense
    requires_hitl_approval=True,
)

