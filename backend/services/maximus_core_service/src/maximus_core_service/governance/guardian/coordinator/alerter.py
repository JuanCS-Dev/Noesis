"""Alert Manager Module.

Handles critical alerts and veto escalations.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from ..base import ConstitutionalViolation, VetoAction

logger = logging.getLogger(__name__)


class AlertManager:
    """Manages critical alerts and escalations.

    Responsible for sending critical alerts to external channels
    and escalating veto situations requiring human oversight.

    Attributes:
        coordinator_id: ID of the coordinator.
        critical_alert_channels: External alert channels.
        alert_file: Path to alert log file.
    """

    def __init__(
        self,
        coordinator_id: str,
        alert_file: str | Path = "/tmp/guardian_critical_alerts.json",
    ) -> None:
        """Initialize alert manager.

        Args:
            coordinator_id: Coordinator identifier.
            alert_file: Path to alert log file.
        """
        self.coordinator_id = coordinator_id
        self.critical_alert_channels: list[str] = []
        self.alert_file = Path(alert_file)

    async def send_critical_alert(
        self,
        violation: ConstitutionalViolation,
    ) -> dict[str, Any]:
        """Send critical alert to external channels.

        Args:
            violation: The critical violation.

        Returns:
            Alert data that was sent.
        """
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "severity": "CRITICAL",
            "violation": violation.to_dict(),
            "coordinator_id": self.coordinator_id,
        }

        logger.critical(
            "CRITICAL ALERT: %s",
            violation.description,
        )

        self._write_alert_to_file(alert)
        await self._send_to_channels(alert)

        return alert

    async def escalate_vetos(
        self,
        vetos: list[VetoAction],
    ) -> dict[str, Any]:
        """Escalate multiple vetos to human oversight.

        Args:
            vetos: List of vetos requiring escalation.

        Returns:
            Escalation data.
        """
        escalation = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "veto_escalation",
            "veto_count": len(vetos),
            "vetos": [v.to_dict() for v in vetos],
            "message": "Multiple vetos require human review",
            "coordinator_id": self.coordinator_id,
        }

        logger.warning(
            "ESCALATION: %d vetos require human review",
            len(vetos),
        )

        self._write_alert_to_file(escalation)

        return escalation

    def _write_alert_to_file(self, alert: dict[str, Any]) -> None:
        """Write alert to log file.

        Args:
            alert: Alert data to write.
        """
        alerts = []

        if self.alert_file.exists():
            try:
                alerts = json.loads(
                    self.alert_file.read_text(encoding="utf-8")
                )
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to read existing alerts: %s", e)

        alerts.append(alert)

        try:
            self.alert_file.write_text(
                json.dumps(alerts, indent=2),
                encoding="utf-8",
            )
        except OSError as e:
            logger.error("Failed to write alert to file: %s", e)

    async def _send_to_channels(self, alert: dict[str, Any]) -> None:
        """Send alert to configured channels.

        Args:
            alert: Alert data to send.

        Note:
            In production, would send to:
            - Slack/Discord
            - PagerDuty
            - Email
            - SIEM
        """
        for channel in self.critical_alert_channels:
            logger.info(
                "Would send alert to channel: %s",
                channel,
            )

    def add_alert_channel(self, channel: str) -> None:
        """Add an alert channel.

        Args:
            channel: Channel identifier to add.
        """
        if channel not in self.critical_alert_channels:
            self.critical_alert_channels.append(channel)

    def remove_alert_channel(self, channel: str) -> None:
        """Remove an alert channel.

        Args:
            channel: Channel identifier to remove.
        """
        if channel in self.critical_alert_channels:
            self.critical_alert_channels.remove(channel)
