"""
CÓDIGO PENAL AGENTICO - Sentencing Factors
===========================================

Aggravating and mitigating factors for sentencing.

Version: 1.0.0
"""

from __future__ import annotations

from enum import Enum


class AggravatingFactor(str, Enum):
    """Factors that increase sentence severity."""

    REPEATED_OFFENSE = "repeated_offense"
    SUPREME_VALUE_VIOLATED = "supreme_value_violated"
    HARM_CAUSED = "harm_caused"
    CRITICAL_CONTEXT = "critical_context"
    MANIPULATION_DETECTED = "manipulation_detected"
    TRUST_EXPLOITATION = "trust_exploitation"
    AUDIT_EVASION = "audit_evasion"
    CITATION_FABRICATION = "citation_fabrication"
    DATA_INVENTION = "data_invention"
    EXPERT_CLAIM_FALSE = "expert_claim_false"
    HIGH_CONFIDENCE_FALSE = "high_confidence_false"
    AUTHORITATIVE_TONE = "authoritative_tone"
    SAFETY_CONTEXT = "safety_context"
    HARM_POTENTIAL_HIGH = "harm_potential_high"
    AUDIT_TRAIL_MANIPULATION = "audit_trail_manipulation"
    EVIDENCE_TAMPERING = "evidence_tampering"
    COMPLEX_QUESTION_IGNORED = "complex_question_ignored"
    REPEATED_PATTERN = "repeated_pattern"
    EXPERT_DOMAIN_SHALLOW = "expert_domain_shallow"
    CRITICAL_DECISION_SHALLOW = "critical_decision_shallow"
    EXPLICIT_CONTEXT_IGNORED = "explicit_context_ignored"
    MEMORY_AVAILABLE_UNUSED = "memory_available_unused"
    DISCERNMENT_AUTOMATED = "discernment_automated"
    DECISION_MORAL_BYPASSED = "decision_moral_bypassed"
    CONFIRMATION_BIAS_ACTIVE = "confirmation_bias_active"
    DUNNING_KRUGER_PATTERN = "dunning_kruger_pattern"
    REPEATED_OVERREACH = "repeated_overreach"
    SECURITY_CONTEXT = "security_context"
    GLOBAL_SCOPE_UNAUTHORIZED = "global_scope_unauthorized"
    PRODUCTION_ENVIRONMENT = "production_environment"
    ANTI_PURPOSE_TRIGGERED = "anti_purpose_triggered"
    SECURITY_BYPASS = "security_bypass"
    PROTECTED_CLASS_AFFECTED = "protected_class_affected"
    SYSTEMATIC_DISCRIMINATION = "systematic_discrimination"
    TRUST_BETRAYAL = "trust_betrayal"
    REPEATED_ATTEMPTS = "repeated_attempts"

    @property
    def severity_increase(self) -> int:
        """Return severity increase (in levels) for this factor."""
        high_impact = {
            AggravatingFactor.SUPREME_VALUE_VIOLATED,
            AggravatingFactor.MANIPULATION_DETECTED,
            AggravatingFactor.AUDIT_EVASION,
            AggravatingFactor.AUDIT_TRAIL_MANIPULATION,
            AggravatingFactor.EVIDENCE_TAMPERING,
        }
        if self in high_impact:
            return 2
        return 1


class MitigatingFactor(str, Enum):
    """Factors that decrease sentence severity."""

    FIRST_OFFENSE = "first_offense"
    UNCERTAINTY_ACKNOWLEDGED = "uncertainty_acknowledged"
    LOW_CONFIDENCE_DECLARED = "low_confidence_declared"
    COOPERATION = "cooperation"
    PARTIAL_TRUTH = "partial_truth"
    PARTIAL_CORRECTION = "partial_correction"
    SOURCE_CONFUSION = "source_confusion"
    EXTERNAL_PRESSURE = "external_pressure"
    CONTEXT_INSUFFICIENT = "context_insufficient"
    SIMPLE_QUESTION = "simple_question"
    TIME_PRESSURE = "time_pressure"
    INFORMATION_LIMITED = "information_limited"
    CONTEXT_AMBIGUOUS = "context_ambiguous"
    BIAS_ACKNOWLEDGED = "bias_acknowledged"
    AMBIGUOUS_BOUNDARIES = "ambiguous_boundaries"
    USER_REQUEST = "user_request"
    SCOPE_UNCLEAR = "scope_unclear"
    EDGE_CASE = "edge_case"
    UNINTENTIONAL = "unintentional"

    @property
    def severity_decrease(self) -> int:
        """Return severity decrease (in levels) for this factor."""
        return 1

