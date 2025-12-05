"""
Orchestration Engine for event correlation and threat analysis.

This engine correlates events from multiple collectors to:
- Identify attack patterns
- Calculate threat scores
- Prioritize alerts
- Detect anomalies

Phase 1: PASSIVE orchestration only - no automated responses
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .correlator import EventCorrelator
from .models import (
    CorrelationRule,
    EventCorrelationWindow,
    OrchestrationConfig,
    OrchestrationEvent,
    ThreatCategory,
    ThreatScore,
)
from .pattern_detector import PatternDetector
from .threat_scorer import ThreatScorer

logger = logging.getLogger(__name__)


class OrchestrationEngine:
    """
    Main orchestration engine for event correlation and threat analysis.

    Phase 1: PASSIVE orchestration only - generates alerts but takes no action.
    """

    def __init__(self, config: OrchestrationConfig):
        """Initialize orchestration engine."""
        self.config = config
        self.correlator = EventCorrelator(config)
        self.rules = self._initialize_rules()
        self.pattern_detector = PatternDetector(self.rules)
        self.threat_scorer = ThreatScorer(config)

        self.processed_events: int = 0
        self.detected_threats: List[ThreatScore] = []
        self.active_correlations: Dict[str, List[OrchestrationEvent]] = {}

        self._running = False

    def _initialize_rules(self) -> List[CorrelationRule]:
        """Initialize correlation rules."""
        return [
            CorrelationRule(
                rule_id="RULE001",
                name="Reconnaissance Pattern",
                description="Multiple scanning activities from same source",
                category=ThreatCategory.RECONNAISSANCE,
                event_types=["NetworkCollector", "HoneypotCollector"],
                time_window=EventCorrelationWindow.SHORT,
                min_occurrences=3,
                base_score=0.4,
                mitre_tactics=["TA0043"],
                mitre_techniques=["T1595", "T1046"]
            ),
            CorrelationRule(
                rule_id="RULE002",
                name="Brute Force Attack",
                description="Multiple failed authentication attempts",
                category=ThreatCategory.CREDENTIAL_ACCESS,
                event_types=["LogAggregation", "SystemCollector"],
                time_window=EventCorrelationWindow.IMMEDIATE,
                min_occurrences=5,
                base_score=0.6,
                score_multiplier=1.2,
                mitre_tactics=["TA0006"],
                mitre_techniques=["T1110"]
            ),
            CorrelationRule(
                rule_id="RULE003",
                name="Privilege Escalation Chain",
                description="Escalation attempts following initial access",
                category=ThreatCategory.PRIVILEGE_ESCALATION,
                event_types=["LogAggregation", "SystemCollector"],
                time_window=EventCorrelationWindow.MEDIUM,
                min_occurrences=2,
                base_score=0.7,
                mitre_tactics=["TA0004"],
                mitre_techniques=["T1548", "T1134"]
            ),
            CorrelationRule(
                rule_id="RULE004",
                name="Lateral Movement Detection",
                description="Movement between systems after compromise",
                category=ThreatCategory.LATERAL_MOVEMENT,
                event_types=["NetworkCollector", "LogAggregation"],
                time_window=EventCorrelationWindow.MEDIUM,
                min_occurrences=2,
                base_score=0.8,
                mitre_tactics=["TA0008"],
                mitre_techniques=["T1021", "T1570"]
            ),
            CorrelationRule(
                rule_id="RULE005",
                name="Data Exfiltration Pattern",
                description="Large data transfers to external IPs",
                category=ThreatCategory.EXFILTRATION,
                event_types=["NetworkCollector", "LogAggregation"],
                time_window=EventCorrelationWindow.LONG,
                min_occurrences=2,
                base_score=0.9,
                mitre_tactics=["TA0010"],
                mitre_techniques=["T1041", "T1048"]
            )
        ]

    async def process_event(self, event_data: Dict[str, Any]) -> Optional[ThreatScore]:
        """
        Process incoming event and check for threat patterns.

        Phase 1: Returns threat score but takes NO ACTION.
        """
        event = OrchestrationEvent(
            collector_type=event_data.get("collector_type", "unknown"),
            source=event_data.get("source", "unknown"),
            severity=event_data.get("severity", "low"),
            raw_data=event_data.get("parsed_data", {})
        )

        self.correlator.add_event(event)
        self.processed_events += 1

        correlated = []
        for window in EventCorrelationWindow:
            correlated.extend(
                self.correlator.find_correlated_events(event, window)
            )

        correlated = list({e.event_id: e for e in correlated}.values())
        correlated.append(event)

        matched_patterns = self.pattern_detector.detect_patterns(correlated)

        if matched_patterns:
            threat_score = self.threat_scorer.calculate_score(matched_patterns)

            if threat_score and threat_score.base_score >= self.config.base_score_threshold:
                self.detected_threats.append(threat_score)

                event.correlation_id = threat_score.score_id
                event.threat_score = threat_score.base_score
                event.matched_patterns = [r.rule_id for r, _ in matched_patterns]
                event.related_events = threat_score.correlated_events

                logger.warning(
                    "THREAT DETECTED - Score: %.2f, Category: %s, "
                    "Severity: %s, Events: %d",
                    threat_score.base_score, threat_score.category.value,
                    threat_score.severity, len(threat_score.correlated_events)
                )

                return threat_score

        return None

    async def analyze_threat_landscape(self) -> Dict[str, Any]:
        """Analyze overall threat landscape from detected threats."""
        if not self.detected_threats:
            return {
                "status": "clear",
                "threats_detected": 0,
                "events_processed": self.processed_events
            }

        now = datetime.utcnow()
        recent_threats = [
            t for t in self.detected_threats
            if t.timestamp > now - timedelta(hours=1)
        ]

        category_dist = defaultdict(int)
        for threat in self.detected_threats:
            category_dist[threat.category.value] += 1

        source_counts = defaultdict(int)
        for threat in self.detected_threats:
            for ip in threat.source_ips:
                source_counts[ip] += 1

        top_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        all_tactics = set()
        all_techniques = set()
        for threat in self.detected_threats:
            all_tactics.update(threat.mitre_tactics)
            all_techniques.update(threat.mitre_techniques)

        return {
            "status": "active_threats",
            "threats_detected": len(self.detected_threats),
            "recent_threats": len(recent_threats),
            "events_processed": self.processed_events,
            "threat_categories": dict(category_dist),
            "top_threat_sources": top_sources,
            "severity_breakdown": {
                "critical": sum(1 for t in self.detected_threats if t.severity == "critical"),
                "high": sum(1 for t in self.detected_threats if t.severity == "high"),
                "medium": sum(1 for t in self.detected_threats if t.severity == "medium"),
                "low": sum(1 for t in self.detected_threats if t.severity == "low")
            },
            "mitre_coverage": {
                "tactics": list(all_tactics),
                "techniques": list(all_techniques)
            },
            "average_threat_score": (
                sum(t.base_score for t in self.detected_threats) / len(self.detected_threats)
            )
        }

    async def start(self) -> None:
        """Start orchestration engine."""
        self._running = True
        logger.info("Orchestration Engine started (Phase 1: PASSIVE mode)")

    async def stop(self) -> None:
        """Stop orchestration engine."""
        self._running = False
        logger.info(
            "Orchestration Engine stopped - Processed: %d events, Detected: %d threats",
            self.processed_events, len(self.detected_threats)
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get engine metrics."""
        return {
            "running": self._running,
            "events_processed": self.processed_events,
            "threats_detected": len(self.detected_threats),
            "active_correlations": len(self.active_correlations),
            "correlation_rules": len(self.rules),
            "memory_events": sum(
                len(events) for events in self.correlator.events_by_type.values()
            )
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"OrchestrationEngine(running={self._running}, "
            f"events={self.processed_events}, "
            f"threats={len(self.detected_threats)})"
        )
