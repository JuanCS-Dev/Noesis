"""
Incident Management for CANDI Core.

Incident creation and tracking.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from .models import AnalysisResult, Incident

logger = logging.getLogger(__name__)


class IncidentMixin:
    """Mixin providing incident management capabilities."""

    active_incidents: Dict[str, Incident]
    incident_counter: int
    stats: Dict[str, Any]

    def _create_or_update_incident(
        self,
        event: Dict[str, Any],
        result: AnalysisResult,
    ) -> Incident:
        """Create new incident or update existing one."""
        # Try to find related incident (same source IP, within 24h)
        source_ip = event.get('source_ip')
        cutoff_time = datetime.now() - timedelta(hours=24)

        for incident in self.active_incidents.values():
            if (
                any(e.get('source_ip') == source_ip for e in incident.events)
                and incident.created_at > cutoff_time
            ):
                # Update existing incident
                incident.add_event(event)
                incident.escalate(result.threat_level)
                if result.attribution.attributed_actor:
                    incident.attributed_actor = result.attribution.attributed_actor
                return incident

        # Create new incident
        self.incident_counter += 1
        incident_id = (
            f"INC-{datetime.now().strftime('%Y%m%d')}-{self.incident_counter:04d}"
        )

        incident = Incident(incident_id, event)
        incident.threat_level = result.threat_level
        if result.attribution.attributed_actor:
            incident.attributed_actor = result.attribution.attributed_actor

        self.active_incidents[incident_id] = incident
        self.stats["active_incidents"] += 1

        logger.info("Created incident %s for %s", incident_id, source_ip)

        return incident

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        """Get incident by ID."""
        return self.active_incidents.get(incident_id)

    def get_active_incidents(self) -> list[Dict[str, Any]]:
        """Get all active incidents."""
        return [incident.to_dict() for incident in self.active_incidents.values()]
