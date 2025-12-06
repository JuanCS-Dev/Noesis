"""
Event Correlator for Orchestration Engine.

Correlates events to identify patterns.
"""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List

from .models import EventCorrelationWindow, OrchestrationConfig, OrchestrationEvent


class EventCorrelator:
    """Correlates events to identify patterns."""

    def __init__(self, config: OrchestrationConfig):
        """Initialize event correlator."""
        self.config = config
        self.events_by_type: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        self.events_by_source: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        self.correlation_cache: Dict[str, List[OrchestrationEvent]] = {}

    def add_event(self, event: OrchestrationEvent) -> None:
        """Add event to correlation windows."""
        self.events_by_type[event.collector_type].append(event)

        if "source_ip" in event.raw_data:
            self.events_by_source[event.raw_data["source_ip"]].append(event)

        self._clean_old_events()

    def find_correlated_events(
        self,
        event: OrchestrationEvent,
        window: EventCorrelationWindow
    ) -> List[OrchestrationEvent]:
        """Find events correlated with the given event."""
        correlated = []
        cutoff = event.timestamp - timedelta(minutes=window.value)

        if "source_ip" in event.raw_data:
            source_ip = event.raw_data["source_ip"]
            for e in self.events_by_source.get(source_ip, []):
                if e.timestamp >= cutoff and e.event_id != event.event_id:
                    correlated.append(e)

        if "target" in event.raw_data:
            target = event.raw_data["target"]
            for events in self.events_by_type.values():
                for e in events:
                    if (e.timestamp >= cutoff and
                        e.raw_data.get("target") == target and
                        e.event_id != event.event_id):
                        correlated.append(e)

        return correlated

    def _clean_old_events(self) -> None:
        """Remove events older than TTL."""
        cutoff = datetime.utcnow() - timedelta(minutes=self.config.event_ttl_minutes)

        for event_type, events in self.events_by_type.items():
            while events and events[0].timestamp < cutoff:
                events.popleft()

        for source, events in self.events_by_source.items():
            while events and events[0].timestamp < cutoff:
                events.popleft()
