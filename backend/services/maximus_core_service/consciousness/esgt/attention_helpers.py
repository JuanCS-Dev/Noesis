"""
ESGT Attention Helpers - MEA attention-to-salience conversion utilities.

Converts MEA attention states into ESGT salience scores and content payloads.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from .models import SalienceScore

if TYPE_CHECKING:
    from consciousness.mea.attention_schema import AttentionState
    from consciousness.mea.boundary_detector import BoundaryAssessment
    from consciousness.mea.self_model import IntrospectiveSummary


def compute_salience_from_attention(
    attention_state: "AttentionState",
    boundary: "BoundaryAssessment | None" = None,
    arousal_level: float | None = None,
) -> SalienceScore:
    """
    Build a SalienceScore from MEA attention outputs.

    Args:
        attention_state: Current attention state from MEA
        boundary: Optional boundary assessment for urgency calculation
        arousal_level: Optional arousal level override

    Returns:
        SalienceScore computed from attention metrics
    """
    primary_score = (
        attention_state.salience_order[0][1]
        if attention_state.salience_order
        else attention_state.confidence
    )
    novelty = max(0.0, min(1.0, abs(primary_score - attention_state.baseline_intensity)))

    focus = attention_state.focus_target.lower()
    relevance = 0.6
    if focus.startswith(("threat", "alert", "incident", "escalation")):
        relevance = 0.9
    elif focus.startswith(("maintenance", "health", "self-care")):
        relevance = 0.7

    urgency = 0.5
    if boundary is not None:
        urgency = max(0.1, min(1.0, 1.0 - boundary.stability))

    if arousal_level is not None:
        urgency = max(urgency, min(1.0, arousal_level))

    salience_score = SalienceScore(
        novelty=novelty,
        relevance=relevance,
        urgency=urgency,
        confidence=attention_state.confidence,
    )

    modality_weights = list(attention_state.modality_weights.values())
    if modality_weights:
        dominance = max(modality_weights)
        salience_score.delta = min(0.25, 0.15 + max(0.0, dominance - 0.5) * 0.4)

    return salience_score


def build_content_from_attention(
    attention_state: "AttentionState",
    summary: "IntrospectiveSummary | None" = None,
) -> dict[str, Any]:
    """
    Construct ESGT content payload using MEA attention and self narrative.

    Args:
        attention_state: Current attention state from MEA
        summary: Optional introspective summary for self-narrative

    Returns:
        Content dictionary for ESGT broadcast
    """
    content: dict[str, Any] = {
        "type": "attention_focus",
        "focus_target": attention_state.focus_target,
        "confidence": attention_state.confidence,
        "modalities": attention_state.modality_weights,
        "baseline_intensity": attention_state.baseline_intensity,
        "salience_ranking": attention_state.salience_order,
    }

    if summary is not None:
        content["self_narrative"] = summary.narrative
        content["self_confidence"] = summary.confidence
        content["perspective"] = {
            "viewpoint": summary.perspective.viewpoint,
            "orientation": summary.perspective.orientation,
            "timestamp": summary.perspective.timestamp.isoformat(),
        }

    return content
