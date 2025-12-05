"""
Threat Scorer for Orchestration Engine.

Calculates threat scores for correlated events.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, List, Optional, Tuple

from .models import CorrelationRule, OrchestrationConfig, OrchestrationEvent, ThreatScore


class ThreatScorer:
    """Calculates threat scores for correlated events."""

    def __init__(self, config: OrchestrationConfig):
        """Initialize threat scorer."""
        self.config = config

    def calculate_score(
        self,
        matched_patterns: List[Tuple[CorrelationRule, List[OrchestrationEvent]]]
    ) -> Optional[ThreatScore]:
        """Calculate threat score from matched patterns."""
        if not matched_patterns:
            return None

        total_score = 0.0
        all_events = []
        all_rules = []
        tactics = set()
        techniques = set()
        sources = set()
        targets = set()
        timeline = []

        for rule, events in matched_patterns:
            rule_score = rule.base_score * rule.score_multiplier
            event_factor = min(len(events) / rule.min_occurrences, 2.0)
            total_score += rule_score * event_factor

            all_events.extend([e.event_id for e in events])
            all_rules.append(rule.rule_id)
            tactics.update(rule.mitre_tactics)
            techniques.update(rule.mitre_techniques)

            for event in events:
                if "source_ip" in event.raw_data:
                    sources.add(event.raw_data["source_ip"])
                if "target" in event.raw_data:
                    targets.add(event.raw_data["target"])
                timeline.append((event.timestamp, event.collector_type))

        final_score = min(total_score, 1.0)

        if final_score >= self.config.critical_score_threshold:
            severity = "critical"
        elif final_score >= 0.6:
            severity = "high"
        elif final_score >= 0.4:
            severity = "medium"
        else:
            severity = "low"

        category_counts = defaultdict(int)
        for rule, _ in matched_patterns:
            category_counts[rule.category] += 1
        category = max(category_counts, key=category_counts.get)

        return ThreatScore(
            base_score=final_score,
            confidence=min(len(matched_patterns) / 3.0, 1.0),
            severity=severity,
            category=category,
            correlated_events=all_events,
            matched_rules=all_rules,
            source_ips=sources,
            target_systems=targets,
            attack_timeline=sorted(timeline),
            mitre_tactics=tactics,
            mitre_techniques=techniques
        )
