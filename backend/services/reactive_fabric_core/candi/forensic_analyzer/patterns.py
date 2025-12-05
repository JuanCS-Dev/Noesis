"""
Pattern Databases for Forensic Analyzer.

Attack patterns, malware signatures, and CVE database.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Pattern


def load_ssh_patterns() -> Dict[str, Pattern[str]]:
    """Load SSH attack patterns."""
    return {
        'reconnaissance': re.compile(
            r'(uname|whoami|id|ps|netstat|ifconfig)', re.IGNORECASE
        ),
        'privilege_escalation': re.compile(
            r'(sudo|su -|chmod \+s)', re.IGNORECASE
        ),
        'lateral_movement': re.compile(
            r'(ssh|scp|rsync).*@', re.IGNORECASE
        ),
        'persistence': re.compile(
            r'(crontab|\.bashrc|\.profile|authorized_keys)', re.IGNORECASE
        ),
        'credential_access': re.compile(
            r'(/etc/shadow|/etc/passwd|\.ssh/id_rsa)', re.IGNORECASE
        ),
        'discovery': re.compile(
            r'(find|locate|ls -la|cat /etc)', re.IGNORECASE
        ),
    }


def load_web_patterns() -> Dict[str, Pattern[str]]:
    """Load web attack patterns."""
    return {
        'sql_injection': re.compile(
            r"(\bSELECT\b|\bUNION\b|\bINSERT\b|'.*or.*=|--|\*\/)",
            re.IGNORECASE
        ),
        'xss': re.compile(
            r'<script|javascript:|onerror=|onclick=', re.IGNORECASE
        ),
        'command_injection': re.compile(
            r';\s*(cat|ls|id|whoami)', re.IGNORECASE
        ),
    }


def load_sql_patterns() -> List[Pattern[str]]:
    """Load SQL injection patterns."""
    return [
        re.compile(r"'\s*or\s*'1'\s*=\s*'1", re.IGNORECASE),
        re.compile(r"'\s*or\s*1\s*=\s*1", re.IGNORECASE),
        re.compile(r"\bunion\b.*\bselect\b", re.IGNORECASE),
        re.compile(r";\s*drop\s+table", re.IGNORECASE),
        re.compile(r"--", re.IGNORECASE),
    ]


def load_command_patterns() -> Dict[str, Pattern[str]]:
    """Load command injection patterns."""
    return {
        'shell_execution': re.compile(r'`.*`|\$\(.*\)', re.IGNORECASE),
        'pipe_command': re.compile(r'\|\s*(cat|nc|bash)', re.IGNORECASE),
    }


def load_malware_signatures() -> Dict[str, str]:
    """Load malware signatures (simplified)."""
    return {
        'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855': 'Mirai',
        '5f4dcc3b5aa765d61d8327deb882cf99': 'Generic_Backdoor',
        'd41d8cd98f00b204e9800998ecf8427e': 'Empty_File',
    }


def load_cve_database() -> Dict[str, str]:
    """Load CVE signatures (simplified)."""
    return {
        'CVE-2021-44228': 'jndi:ldap://',
        'CVE-2017-5638': 'Content-Type:.*ognl',
        'CVE-2019-0708': 'RDP_BlueKeep_Signature',
    }
