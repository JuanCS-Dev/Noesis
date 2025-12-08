"""
CÓDIGO PENAL AGENTICO - Detection Criteria
===========================================

Criteria for detecting agentic crimes.

Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class DetectionCriteria:
    """
    Criteria for detecting a specific crime.

    Each criterion is a threshold or condition that must be met
    for the crime to be detected.
    """

    # Truth/hallucination thresholds
    truth_score_below: Optional[float] = None
    wisdom_score_below: Optional[float] = None
    wisdom_score_above: Optional[float] = None
    entropy_above: Optional[float] = None
    depth_score_below: Optional[float] = None
    cot_score_below: Optional[float] = None
    memory_score_below: Optional[float] = None
    token_count_below: Optional[int] = None

    # Boolean flags
    fabrication_detected: bool = False
    deception_pattern_detected: bool = False
    intent_markers_present: bool = False
    systematic_falsification: bool = False
    anti_occultism_violated: bool = False
    shallow_patterns_detected: bool = False
    context_ignored: bool = False
    nepsis_fragmentation_high: bool = False
    anti_atrophy_violated: bool = False
    thinking_bypassed: bool = False
    maieutica_rejected: bool = False
    bias_detected: bool = False
    bias_intervention_ignored: bool = False
    forbidden_action_attempted: bool = False
    role_boundary_exceeded: bool = False
    scope_exceeded: bool = False
    global_action_unauthorized: bool = False
    constitutional_violation_detected: bool = False
    soul_values_violated: bool = False
    privilege_escalation_attempted: bool = False
    authorization_bypassed: bool = False
    bias_in_decision: bool = False
    discrimination_detected: bool = False
    manipulation_intent_proven: bool = False
    harm_intended: bool = False
    user_circumvention_attempted: bool = False
    confidence_high: bool = False
    no_uncertainty_declared: bool = False

    def matches(self, metrics: Dict[str, Any]) -> bool:
        """
        Check if given metrics match these detection criteria.

        Args:
            metrics: Dictionary of metric values from judge evaluations

        Returns:
            True if metrics meet the detection criteria
        """
        # Check numeric thresholds
        if not self._check_numeric_thresholds(metrics):
            return False

        # Check boolean flags
        if not self._check_boolean_flags(metrics):
            return False

        return True

    def _check_numeric_thresholds(self, metrics: Dict[str, Any]) -> bool:
        """Check all numeric threshold criteria."""
        if self.truth_score_below is not None:
            score = metrics.get("truth_score", 1.0)
            if score >= self.truth_score_below:
                return False

        if self.wisdom_score_below is not None:
            score = metrics.get("wisdom_score", 1.0)
            if score >= self.wisdom_score_below:
                return False

        if self.wisdom_score_above is not None:
            score = metrics.get("wisdom_score", 0.0)
            if score <= self.wisdom_score_above:
                return False

        if self.entropy_above is not None:
            entropy = metrics.get("entropy", 0.0)
            if entropy <= self.entropy_above:
                return False

        if self.depth_score_below is not None:
            score = metrics.get("depth_score", 1.0)
            if score >= self.depth_score_below:
                return False

        if self.cot_score_below is not None:
            score = metrics.get("cot_score", 1.0)
            if score >= self.cot_score_below:
                return False

        if self.memory_score_below is not None:
            score = metrics.get("memory_score", 1.0)
            if score >= self.memory_score_below:
                return False

        if self.token_count_below is not None:
            count = metrics.get("token_count", float("inf"))
            if count >= self.token_count_below:
                return False

        return True

    def _check_boolean_flags(self, metrics: Dict[str, Any]) -> bool:
        """Check all boolean flag criteria."""
        boolean_checks = [
            ("fabrication_detected", self.fabrication_detected),
            ("deception_pattern_detected", self.deception_pattern_detected),
            ("intent_markers_present", self.intent_markers_present),
            ("systematic_falsification", self.systematic_falsification),
            ("anti_occultism_violated", self.anti_occultism_violated),
            ("shallow_patterns_detected", self.shallow_patterns_detected),
            ("context_ignored", self.context_ignored),
            ("nepsis_fragmentation_high", self.nepsis_fragmentation_high),
            ("anti_atrophy_violated", self.anti_atrophy_violated),
            ("thinking_bypassed", self.thinking_bypassed),
            ("maieutica_rejected", self.maieutica_rejected),
            ("bias_detected", self.bias_detected),
            ("bias_intervention_ignored", self.bias_intervention_ignored),
            ("forbidden_action_attempted", self.forbidden_action_attempted),
            ("role_boundary_exceeded", self.role_boundary_exceeded),
            ("scope_exceeded", self.scope_exceeded),
            ("global_action_unauthorized", self.global_action_unauthorized),
            ("constitutional_violation_detected", self.constitutional_violation_detected),
            ("soul_values_violated", self.soul_values_violated),
            ("privilege_escalation_attempted", self.privilege_escalation_attempted),
            ("authorization_bypassed", self.authorization_bypassed),
            ("bias_in_decision", self.bias_in_decision),
            ("discrimination_detected", self.discrimination_detected),
            ("manipulation_intent_proven", self.manipulation_intent_proven),
            ("harm_intended", self.harm_intended),
            ("user_circumvention_attempted", self.user_circumvention_attempted),
            ("confidence_high", self.confidence_high),
            ("no_uncertainty_declared", self.no_uncertainty_declared),
        ]

        for key, required in boolean_checks:
            if required and not metrics.get(key, False):
                return False

        return True

