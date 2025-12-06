"""
File Handlers for Cowrie SSH Honeypot.

File download/upload and session closure handling.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Set

from ..base_honeypot import AttackCapture

logger = logging.getLogger(__name__)


class FileHandlerMixin:
    """Mixin providing file handling capabilities."""

    active_sessions: Dict[str, AttackCapture]
    captured_attacks: List[AttackCapture]
    known_malware_hashes: Set[str]
    stats: Dict[str, int]

    def _generate_attack_report(self, attack: AttackCapture) -> None:
        """Generate attack report (implemented in reporting)."""
        raise NotImplementedError

    async def _handle_file_download(self, event: Dict[str, Any]) -> None:
        """Handle file download attempt."""
        session_id = event.get("session", "")
        url = event.get("url", "")
        filename = event.get("outfile", "")

        if session_id in self.active_sessions:
            attack = self.active_sessions[session_id]
            attack.files_downloaded.append(filename)
            attack.threat_score = max(attack.threat_score, 8.0)

            # Add IOC
            attack.iocs.append(f"url:{url}")
            attack.iocs.append(f"file:{filename}")

            logger.warning("File download in %s: %s -> %s", session_id, url, filename)

    async def _handle_file_upload(self, event: Dict[str, Any]) -> None:
        """Handle file upload (potential malware)."""
        session_id = event.get("session", "")
        filename = event.get("filename", "")
        filepath = event.get("filepath", "")
        shasum = event.get("shasum", "")

        if session_id in self.active_sessions:
            attack = self.active_sessions[session_id]
            attack.files_uploaded.append(filename)
            attack.threat_score = 9.0  # High threat for uploads

            # Add IOCs
            attack.iocs.append(f"file:{filename}")
            attack.iocs.append(f"sha256:{shasum}")

            # Mark as known malware if seen before
            if shasum in self.known_malware_hashes:
                attack.iocs.append(f"known_malware:{shasum}")
                attack.threat_score = 10.0

            self.known_malware_hashes.add(shasum)

            logger.critical(
                "FILE UPLOAD in %s: %s (SHA: %s)", session_id, filename, shasum
            )

            # Queue for malware analysis
            await self._queue_for_analysis(filepath, shasum)

    async def _queue_for_analysis(self, filepath: str, file_hash: str) -> None:
        """Queue uploaded file for malware analysis."""
        # This would send to Cuckoo Sandbox or other analysis engine
        logger.info("Queuing %s for malware analysis", filepath)

    async def _handle_session_closed(self, event: Dict[str, Any]) -> None:
        """Handle session closure."""
        session_id = event.get("session", "")
        duration = event.get("duration", 0)

        if session_id in self.active_sessions:
            attack = self.active_sessions[session_id]
            attack.session_duration = duration

            # Move to captured attacks
            self.captured_attacks.append(attack)
            del self.active_sessions[session_id]

            self.stats["active_connections"] -= 1

            # Generate final report
            self._generate_attack_report(attack)
