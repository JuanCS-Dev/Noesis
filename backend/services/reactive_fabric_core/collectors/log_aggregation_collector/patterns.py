"""
Security Patterns for Log Aggregation Collector.

Security event detection patterns.
"""

from __future__ import annotations

from typing import List

from .models import SecurityEventPattern


def init_security_patterns() -> List[SecurityEventPattern]:
    """Initialize security event detection patterns."""
    return [
        SecurityEventPattern(
            name="failed_authentication",
            severity="medium",
            patterns=[
                "authentication failed",
                "invalid credentials",
                "login failed",
                "unauthorized access",
            ],
            fields_to_extract=["user", "source_ip", "destination"],
            mitre_techniques=["T1078", "T1110"],
        ),
        SecurityEventPattern(
            name="privilege_escalation",
            severity="high",
            patterns=[
                "privilege escalation",
                "sudo",
                "elevation",
                "administrator access",
            ],
            fields_to_extract=["user", "process", "command"],
            mitre_techniques=["T1548", "T1134"],
        ),
        SecurityEventPattern(
            name="suspicious_command",
            severity="high",
            patterns=[
                "wget",
                "curl",
                "nc",
                "netcat",
                "/etc/passwd",
                "/etc/shadow",
                "base64",
                "eval",
                "exec",
            ],
            fields_to_extract=["command", "user", "process_id"],
            mitre_techniques=["T1059", "T1105"],
        ),
        SecurityEventPattern(
            name="network_scanning",
            severity="medium",
            patterns=[
                "port scan",
                "network discovery",
                "nmap",
                "masscan",
                "zmap",
            ],
            fields_to_extract=["source_ip", "destination_ports", "tool"],
            mitre_techniques=["T1046", "T1595"],
        ),
        SecurityEventPattern(
            name="data_exfiltration",
            severity="critical",
            patterns=[
                "data transfer",
                "large upload",
                "suspicious outbound",
                "exfiltration",
            ],
            fields_to_extract=["source", "destination", "bytes_transferred"],
            mitre_techniques=["T1041", "T1048"],
        ),
        SecurityEventPattern(
            name="malware_indicators",
            severity="critical",
            patterns=[
                "malware",
                "virus",
                "trojan",
                "ransomware",
                "backdoor",
                "c2 communication",
            ],
            fields_to_extract=["file_hash", "process_name", "source"],
            mitre_techniques=["T1055", "T1571"],
        ),
    ]
