"""
PFC Integration - Social signal processing through PrefrontalCortex.

TRACK 1: Social Cognition Integration

Processes social signals through PrefrontalCortex for Theory of Mind inference
and compassionate action generation.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from consciousness.prefrontal_cortex import PrefrontalCortex


async def process_social_signal_through_pfc(
    pfc: PrefrontalCortex | None,
    content: dict[str, Any],
    social_signals_counter: list[int],
) -> dict[str, Any] | None:
    """
    Process social signals through PrefrontalCortex if available.

    TRACK 1: Social Cognition Integration

    Detects social content in ESGT broadcasts and routes them through
    the PrefrontalCortex for Theory of Mind inference and compassionate
    action generation.

    Args:
        pfc: PrefrontalCortex instance or None
        content: ESGT content payload to check for social signals
        social_signals_counter: Mutable list to increment counter [0]

    Returns:
        Compassionate response if social signal detected, None otherwise
    """
    if not pfc:
        return None

    # Detect social content types
    content_type = content.get("type", "")
    social_types = [
        "social_interaction",
        "user_message",
        "distress",
        "help_request",
        "attention_focus",  # May contain social narrative
    ]

    if content_type not in social_types:
        return None

    # Extract social indicators
    user_id = content.get("user_id", content.get("agent_id", "unknown"))

    # Build context for PFC
    context = {
        "message": content.get("message", content.get("focus_target", "")),
        "self_narrative": content.get("self_narrative", ""),
        "confidence": content.get("confidence", 0.5),
    }

    # Determine signal type
    signal_type = _determine_signal_type(content, content_type)

    try:
        # Process through PrefrontalCortex
        response = await pfc.process_social_signal(
            user_id=user_id, context=context, signal_type=signal_type
        )

        social_signals_counter[0] += 1

        # Return action if generated
        if response.action:
            return {
                "action": response.action,
                "confidence": response.confidence,
                "reasoning": response.reasoning,
                "tom_prediction": response.tom_prediction,
                "pfc_component": "PrefrontalCortex",
            }

    except Exception as e:
        logger.info("⚠️  PFC processing failed: %s", e)

    return None


def _determine_signal_type(content: dict[str, Any], content_type: str) -> str:
    """Determine the type of social signal from content."""
    if content_type == "distress":
        return "distress"
    if content_type == "help_request":
        return "help_request"
    if content.get("self_narrative"):
        # Check if narrative indicates distress
        narrative = content.get("self_narrative", "").lower()
        if any(word in narrative for word in ["confused", "stuck", "lost", "help", "unsure"]):
            return "distress"
    return "message"
