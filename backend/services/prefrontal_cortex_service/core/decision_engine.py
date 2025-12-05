"""
Prefrontal Cortex Service - Decision Engine
===========================================

Core decision-making logic for executive functions.
"""

from __future__ import annotations

from typing import Any, Dict, List
import uuid

from config import CognitiveSettings
from models.cognitive import Decision
from utils.logging_config import get_logger

logger = get_logger(__name__)


class DecisionEngine:  # pylint: disable=too-few-public-methods
    """
    Makes executive decisions based on context and available options.

    Uses heuristic-based decision-making for task management.

    Attributes:
        settings: Cognitive settings
    """

    def __init__(self, settings: CognitiveSettings):
        """
        Initialize Decision Engine.

        Args:
            settings: Cognitive settings
        """
        self.settings = settings
        logger.info(
            "decision_engine_initialized",
            timeout=settings.decision_timeout
        )

    async def make_decision(
        self,
        context: Dict[str, Any],
        options: List[str]
    ) -> Decision:
        """
        Make a decision based on context and options.

        Uses simple heuristic: prefer options mentioned in context.

        Args:
            context: Decision context
            options: Available options

        Returns:
            Decision with selected option and reasoning
        """
        decision_id = str(uuid.uuid4())

        if not options:
            logger.warning(
                "no_options_available",
                decision_id=decision_id
            )
            return Decision(
                decision_id=decision_id,
                context=context,
                options=[],
                selected_option=None,
                confidence=0.0,
                reasoning="No options available"
            )

        # Simple heuristic: check which option is mentioned in context
        context_str = str(context).lower()
        scores = {
            option: context_str.count(option.lower())
            for option in options
        }

        # Select option with highest score
        selected = max(scores.items(), key=lambda x: x[1])
        selected_option, score = selected

        # If no matches, select first option
        if score == 0:
            selected_option = options[0]
            confidence = 0.3
            reasoning = "Default selection (no context match)"
        else:
            # Normalize confidence based on score
            max_score = max(scores.values())
            confidence = min(0.9, 0.5 + (score / (max_score + 1)) * 0.4)
            reasoning = f"Selected based on context relevance (score: {score})"

        decision = Decision(
            decision_id=decision_id,
            context=context,
            options=options,
            selected_option=selected_option,
            confidence=confidence,
            reasoning=reasoning
        )

        logger.info(
            "decision_made",
            decision_id=decision_id,
            selected=selected_option,
            confidence=confidence
        )

        return decision
