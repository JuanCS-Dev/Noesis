"""
Reporting for Cowrie SSH Honeypot.

Attack report generation.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

from ..base_honeypot import AttackCapture

logger = logging.getLogger(__name__)


class ReportingMixin:
    """Mixin providing reporting capabilities."""

    log_path: Path

    def _generate_attack_report(self, attack: AttackCapture) -> None:
        """Generate detailed attack report."""
        report: Dict[str, Any] = {
            "attack_id": attack.id,
            "timestamp": attack.timestamp.isoformat(),
            "source": f"{attack.source_ip}:{attack.source_port}",
            "duration": attack.session_duration,
            "threat_score": attack.threat_score,
            "attack_stage": attack.attack_stage.value,
            "credentials": attack.credentials_used,
            "commands_executed": len(attack.commands),
            "files_uploaded": len(attack.files_uploaded),
            "files_downloaded": len(attack.files_downloaded),
            "iocs": attack.iocs,
            "ttps": attack.ttps,
            "summary": self._generate_attack_summary(attack),
        }

        # Save report
        report_file = self.log_path / f"reports/attack_{attack.id}.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info("Attack report generated: %s", report_file)

    def _generate_attack_summary(self, attack: AttackCapture) -> str:
        """Generate human-readable attack summary."""
        summary_parts = []

        if attack.threat_score >= 8:
            summary_parts.append("HIGH THREAT ATTACK")
        elif attack.threat_score >= 5:
            summary_parts.append("Medium threat activity")
        else:
            summary_parts.append("Low threat reconnaissance")

        if attack.credentials_used:
            summary_parts.append(
                f"Successful login as {attack.credentials_used.get('username', 'unknown')}"
            )

        if attack.files_uploaded:
            summary_parts.append(
                f"Uploaded {len(attack.files_uploaded)} files (potential malware)"
            )

        if attack.commands:
            summary_parts.append(f"Executed {len(attack.commands)} commands")

        if attack.ttps:
            summary_parts.append(
                f"Detected {len(attack.ttps)} MITRE ATT&CK techniques"
            )

        return ". ".join(summary_parts)
