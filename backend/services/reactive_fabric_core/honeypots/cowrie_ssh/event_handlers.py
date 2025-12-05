"""
Event Handlers for Cowrie SSH Honeypot.

Session and login event processing.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Set

from ..base_honeypot import AttackCapture, AttackStage, HoneypotType

logger = logging.getLogger(__name__)


class EventHandlerMixin:
    """Mixin providing event handling capabilities."""

    honeypot_id: str
    honeypot_type: HoneypotType
    port: int
    telnet_port: int
    active_sessions: Dict[str, AttackCapture]
    stats: Dict[str, int]
    brute_force_attempts: Dict[str, List[Dict[str, Any]]]
    known_malware_hashes: Set[str]

    def _analyze_command(self, command: str) -> float:
        """Analyze command (implemented in command_analysis)."""
        raise NotImplementedError

    def _determine_attack_stage(self, command: str) -> AttackStage:
        """Determine attack stage (implemented in command_analysis)."""
        raise NotImplementedError

    def _extract_ttps_from_command(self, command: str) -> List[str]:
        """Extract TTPs (implemented in command_analysis)."""
        raise NotImplementedError

    def capture_attack(
        self,
        source_ip: str,
        source_port: int,
        attack_stage: AttackStage,
        threat_score: float,
        ttps: List[str],
    ) -> AttackCapture:
        """Capture attack (implemented in base class)."""
        raise NotImplementedError

    async def _process_cowrie_event(self, event: Dict[str, Any]) -> None:
        """Process a single Cowrie event."""
        event_id = event.get("eventid", "")

        if event_id == "cowrie.session.connect":
            await self._handle_new_session(event)

        elif event_id == "cowrie.login.success":
            await self._handle_successful_login(event)

        elif event_id == "cowrie.login.failed":
            await self._handle_failed_login(event)

        elif event_id == "cowrie.command.input":
            await self._handle_command(event)

        elif event_id == "cowrie.session.file_download":
            await self._handle_file_download(event)

        elif event_id == "cowrie.session.file_upload":
            await self._handle_file_upload(event)

        elif event_id == "cowrie.session.closed":
            await self._handle_session_closed(event)

    async def _handle_new_session(self, event: Dict[str, Any]) -> None:
        """Handle new SSH/Telnet session."""
        session_id = event.get("session", "")
        src_ip = event.get("src_ip", "")
        src_port = event.get("src_port", 0)
        protocol = event.get("protocol", "ssh")

        logger.info("New %s session from %s:%d", protocol, src_ip, src_port)

        # Create attack capture
        attack = AttackCapture(
            id=session_id,
            honeypot_id=self.honeypot_id,
            honeypot_type=self.honeypot_type,
            timestamp=datetime.fromisoformat(event.get("timestamp", "")),
            source_ip=src_ip,
            source_port=src_port,
            destination_port=self.port if protocol == "ssh" else self.telnet_port,
            protocol=protocol,
            attack_stage=AttackStage.INITIAL_ACCESS,
            metadata={"session_id": session_id},
        )

        self.active_sessions[session_id] = attack
        self.stats["total_connections"] += 1
        self.stats["active_connections"] += 1

    async def _handle_successful_login(self, event: Dict[str, Any]) -> None:
        """Handle successful login attempt."""
        session_id = event.get("session", "")
        username = event.get("username", "")
        password = event.get("password", "")

        if session_id in self.active_sessions:
            attack = self.active_sessions[session_id]
            attack.credentials_used = {"username": username, "password": password}
            attack.attack_stage = AttackStage.CREDENTIAL_ACCESS

            # High threat score for successful login
            attack.threat_score = 7.0

            logger.warning(
                "Successful login: %s:%s from %s",
                username,
                password,
                attack.source_ip,
            )

            # Add IOC
            attack.iocs.append(f"credential:{username}:{password}")

    async def _handle_failed_login(self, event: Dict[str, Any]) -> None:
        """Handle failed login attempt."""
        src_ip = event.get("src_ip", "")
        username = event.get("username", "")
        password = event.get("password", "")

        # Track brute force attempts
        if src_ip not in self.brute_force_attempts:
            self.brute_force_attempts[src_ip] = []

        self.brute_force_attempts[src_ip].append({
            "timestamp": event.get("timestamp", ""),
            "username": username,
            "password": password,
        })

        # Detect brute force attack
        if len(self.brute_force_attempts[src_ip]) > 10:
            logger.warning("Brute force attack detected from %s", src_ip)

            # Create attack capture for brute force
            self.capture_attack(
                source_ip=src_ip,
                source_port=0,
                attack_stage=AttackStage.CREDENTIAL_ACCESS,
                threat_score=5.0,
                ttps=["T1110 - Brute Force"],
            )

    async def _handle_command(self, event: Dict[str, Any]) -> None:
        """Handle executed command."""
        session_id = event.get("session", "")
        command = event.get("input", "")

        if session_id in self.active_sessions:
            attack = self.active_sessions[session_id]
            attack.commands.append(command)

            # Analyze command for malicious behavior
            threat_level = self._analyze_command(command)

            if threat_level > 0:
                attack.threat_score = max(attack.threat_score, threat_level)
                attack.attack_stage = self._determine_attack_stage(command)

            logger.info("Command executed in %s: %s", session_id, command)

            # Check for specific TTPs
            ttps = self._extract_ttps_from_command(command)
            attack.ttps.extend(ttps)

    async def _handle_file_download(self, event: Dict[str, Any]) -> None:
        """Handle file download attempt (implemented in file_handlers)."""
        raise NotImplementedError

    async def _handle_file_upload(self, event: Dict[str, Any]) -> None:
        """Handle file upload (implemented in file_handlers)."""
        raise NotImplementedError

    async def _handle_session_closed(self, event: Dict[str, Any]) -> None:
        """Handle session closure (implemented in file_handlers)."""
        raise NotImplementedError
