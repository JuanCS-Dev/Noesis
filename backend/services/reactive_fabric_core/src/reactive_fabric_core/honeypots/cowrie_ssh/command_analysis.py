"""
Command Analysis for Cowrie SSH Honeypot.

Command threat analysis and TTP extraction.
"""

from __future__ import annotations

import re
from typing import List

from ..base_honeypot import AttackStage


class CommandAnalysisMixin:
    """Mixin providing command analysis capabilities."""

    def _analyze_command(self, command: str) -> float:
        """
        Analyze command for threat level.

        Returns:
            Threat score (0-10)
        """
        threat_score = 0.0

        # High threat commands
        high_threat = [
            r"wget\s+http",
            r"curl\s+.*\|\s*sh",
            r"chmod\s+\+x",
            r"/etc/passwd",
            r"/etc/shadow",
            r"nc\s+-e",
            r"python\s+-c",
            r"perl\s+-e",
        ]

        # Medium threat commands
        medium_threat = [
            r"uname",
            r"whoami",
            r"id\s",
            r"ps\s+aux",
            r"netstat",
            r"ifconfig",
            r"cat\s+/proc",
        ]

        for pattern in high_threat:
            if re.search(pattern, command, re.IGNORECASE):
                threat_score = max(threat_score, 8.0)
                break

        for pattern in medium_threat:
            if re.search(pattern, command, re.IGNORECASE):
                threat_score = max(threat_score, 5.0)

        return threat_score

    def _determine_attack_stage(self, command: str) -> AttackStage:
        """Determine attack stage from command."""
        if re.search(r"(wget|curl|scp|ftp)", command):
            return AttackStage.EXECUTION
        elif re.search(r"(crontab|systemctl|service)", command):
            return AttackStage.PERSISTENCE
        elif re.search(r"(sudo|su\s|passwd)", command):
            return AttackStage.PRIVILEGE_ESCALATION
        elif re.search(r"(uname|whoami|id\s|hostname)", command):
            return AttackStage.DISCOVERY
        elif re.search(r"(tar|zip|7z|gzip)", command):
            return AttackStage.COLLECTION
        elif re.search(r"(nc|telnet|ssh\s)", command):
            return AttackStage.LATERAL_MOVEMENT
        else:
            return AttackStage.EXECUTION

    def _extract_ttps_from_command(self, command: str) -> List[str]:
        """Extract MITRE ATT&CK TTPs from command."""
        ttps = []

        ttp_patterns = {
            "T1059": r"(bash|sh|cmd|powershell)",  # Command and Scripting Interpreter
            "T1105": r"(wget|curl|scp|ftp)",  # Ingress Tool Transfer
            "T1053": r"(cron|at\s|schtasks)",  # Scheduled Task/Job
            "T1548": r"(sudo|su\s)",  # Abuse Elevation Control Mechanism
            "T1083": r"(find|locate|ls\s)",  # File and Directory Discovery
            "T1057": r"(ps\s|tasklist)",  # Process Discovery
            "T1016": r"(ifconfig|ipconfig|netstat)",  # System Network Config Discovery
            "T1560": r"(tar|zip|rar|7z)",  # Archive Collected Data
            "T1021": r"(ssh\s|telnet|rdp)",  # Remote Services
        }

        for ttp_id, pattern in ttp_patterns.items():
            if re.search(pattern, command, re.IGNORECASE):
                ttps.append(ttp_id)

        return ttps
