"""
Attribution Engine for ML-powered threat actor identification.

Attributes attacks to threat actors based on TTPs, tools, and infrastructure.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from ..forensic_analyzer import ForensicReport
from ..threat_intelligence import ThreatIntelReport
from .database import (
    build_tool_signatures,
    build_ttp_signatures,
    load_infrastructure_database,
    load_threat_actor_database,
)
from .models import AttributionResult
from .scorers import AttributionScorerMixin

logger = logging.getLogger(__name__)


class AttributionEngine(AttributionScorerMixin):
    """
    ML-powered threat actor attribution engine.

    Attribution Factors:
    1. TTP Matching - MITRE ATT&CK technique overlap
    2. Tool Usage - Malware families, exploit frameworks
    3. Infrastructure - IP ranges, hosting providers, domains
    4. Sophistication Level - Attack complexity matching
    """

    def __init__(self):
        """Initialize attribution engine."""
        self._initialized = False

        self.threat_actors = load_threat_actor_database()
        self.ttp_signatures = build_ttp_signatures()
        self.tool_signatures = build_tool_signatures()
        self.infrastructure_db = load_infrastructure_database()

        self.stats = {
            "total_attributions": 0,
            "high_confidence": 0,
            "medium_confidence": 0,
            "low_confidence": 0,
            "apt_detected": 0
        }

    async def initialize(self) -> None:
        """Initialize attribution engine with external resources."""
        if self._initialized:
            return

        logger.info("Initializing Attribution Engine...")
        self._initialized = True
        logger.info("Attribution Engine initialized")

    async def attribute(
        self,
        forensic: ForensicReport,
        intel: ThreatIntelReport
    ) -> AttributionResult:
        """
        Attribute attack to threat actor.

        Args:
            forensic: Forensic analysis report
            intel: Threat intelligence report

        Returns:
            Attribution result with confidence score
        """
        logger.info("Starting attribution for event %s", forensic.event_id)

        result = AttributionResult()

        # Factor 1: TTP Matching (40% weight)
        ttp_scores = self._score_ttp_overlap(forensic, intel)
        result.confidence_factors['ttp_matching'] = max(ttp_scores.values()) if ttp_scores else 0.0

        # Factor 2: Tool Usage (25% weight)
        tool_scores = self._score_tool_usage(forensic, intel)
        result.confidence_factors['tool_usage'] = max(tool_scores.values()) if tool_scores else 0.0

        # Factor 3: Infrastructure (20% weight)
        infra_scores = self._score_infrastructure(forensic, intel)
        result.confidence_factors['infrastructure'] = max(infra_scores.values()) if infra_scores else 0.0

        # Factor 4: Sophistication Level (15% weight)
        sophistication_scores = self._score_sophistication(forensic)
        result.confidence_factors['sophistication'] = max(sophistication_scores.values()) if sophistication_scores else 0.0

        # Aggregate scores
        actor_scores = self._aggregate_scores(
            ttp_scores, tool_scores, infra_scores, sophistication_scores
        )

        # Select best candidate
        if actor_scores:
            best_actor = max(actor_scores, key=actor_scores.get)
            result.attributed_actor = best_actor
            result.confidence = actor_scores[best_actor]

            actor_profile = self.threat_actors.get(best_actor, {})
            result.actor_type = actor_profile.get('type', 'unknown')
            result.motivation = actor_profile.get('motivation', 'unknown')

            result.matching_ttps = self._get_matching_ttps(best_actor, forensic)
            result.matching_tools = self._get_matching_tools(best_actor, forensic, intel)
            result.matching_infrastructure = self._get_matching_infrastructure(best_actor, forensic)

            result.apt_indicators = self._detect_apt_indicators(forensic, intel, actor_profile)

            # Get alternative candidates (top 3)
            sorted_actors = sorted(actor_scores.items(), key=lambda x: x[1], reverse=True)
            for actor, score in sorted_actors[1:4]:
                if score > 30.0:
                    result.alternative_actors.append({
                        'actor': actor,
                        'confidence': score,
                        'type': self.threat_actors.get(actor, {}).get('type', 'unknown')
                    })

        # Update statistics
        self.stats["total_attributions"] += 1
        if result.confidence >= 70:
            self.stats["high_confidence"] += 1
        elif result.confidence >= 40:
            self.stats["medium_confidence"] += 1
        else:
            self.stats["low_confidence"] += 1

        if result.apt_indicators:
            self.stats["apt_detected"] += 1

        logger.info(
            "Attribution complete: %s (confidence: %.1f%%, type: %s)",
            result.attributed_actor or 'unknown', result.confidence, result.actor_type
        )

        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get attribution statistics."""
        return self.stats.copy()
