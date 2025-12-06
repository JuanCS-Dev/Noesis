"""
Pattern Detector for Orchestration Engine.

Detects attack patterns in event streams.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

from .models import CorrelationRule, OrchestrationEvent, ThreatCategory


class PatternDetector:
    """Detects attack patterns in event streams."""

    def __init__(self, rules: List[CorrelationRule]):
        """Initialize pattern detector."""
        self.rules = rules
        self.pattern_cache: Dict[str, List[str]] = {}

    def detect_patterns(
        self,
        events: List[OrchestrationEvent]
    ) -> List[Tuple[CorrelationRule, List[OrchestrationEvent]]]:
        """Detect patterns matching correlation rules."""
        matched_patterns = []

        for rule in self.rules:
            matching_events = self._match_rule(rule, events)
            if len(matching_events) >= rule.min_occurrences:
                matched_patterns.append((rule, matching_events))

        return matched_patterns

    def _match_rule(
        self,
        rule: CorrelationRule,
        events: List[OrchestrationEvent]
    ) -> List[OrchestrationEvent]:
        """Check if events match a correlation rule."""
        matching = []

        for event in events:
            if event.collector_type not in rule.event_types:
                continue

            cutoff = datetime.utcnow() - timedelta(minutes=rule.time_window.value)
            if event.timestamp < cutoff:
                continue

            if self._matches_category_pattern(rule.category, event):
                matching.append(event)

        return matching

    def _matches_category_pattern(
        self,
        category: ThreatCategory,
        event: OrchestrationEvent
    ) -> bool:
        """Check if event matches category-specific patterns."""
        patterns = {
            ThreatCategory.RECONNAISSANCE: [
                "port_scan", "network_discovery", "enumeration", "scanning"
            ],
            ThreatCategory.INITIAL_ACCESS: [
                "authentication", "exploit", "phishing", "login"
            ],
            ThreatCategory.CREDENTIAL_ACCESS: [
                "authentication", "password", "credential", "login", "failed"
            ],
            ThreatCategory.PRIVILEGE_ESCALATION: [
                "sudo", "elevation", "privilege", "escalation", "admin"
            ],
            ThreatCategory.LATERAL_MOVEMENT: [
                "remote", "rdp", "ssh", "smb", "lateral"
            ],
            ThreatCategory.EXFILTRATION: [
                "upload", "transfer", "exfiltration", "data", "bytes_transferred"
            ]
        }

        category_patterns = patterns.get(category, [])
        event_str = str(event.raw_data).lower()

        return any(pattern in event_str for pattern in category_patterns)
