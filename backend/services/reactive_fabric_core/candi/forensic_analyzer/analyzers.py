"""
Analysis Methods for Forensic Analyzer.

Network, behavior, payload, and temporal analysis.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Pattern

from .models import ForensicReport


class AnalyzerMixin:
    """Mixin providing analysis capabilities."""

    ssh_patterns: Dict[str, Pattern[str]]
    web_patterns: Dict[str, Pattern[str]]
    sql_patterns: List[Pattern[str]]
    malware_signatures: Dict[str, str]
    cve_database: Dict[str, str]

    async def _analyze_network(self, event: Dict[str, Any], report: ForensicReport) -> None:
        """Analyze network-level indicators."""
        report.user_agent = event.get('user_agent')
        report.connection_duration = event.get('session_duration', 0.0)
        report.bytes_transferred = event.get('bytes_transferred', 0)

        if report.user_agent:
            suspicious_agents = [
                'sqlmap', 'nikto', 'masscan', 'nmap', 'metasploit',
                'burp', 'zap', 'acunetix', 'nessus'
            ]
            if any(agent in report.user_agent.lower() for agent in suspicious_agents):
                report.behaviors.append('scanner_user_agent')
                report.attack_stages.append('reconnaissance')

        if report.connection_duration < 1.0 and report.bytes_transferred > 1000:
            report.behaviors.append('high_speed_data_exfiltration')
            report.attack_stages.append('exfiltration')

    async def _analyze_ssh_behavior(self, event: Dict[str, Any], report: ForensicReport) -> None:
        """Analyze SSH/Telnet attack behavior."""
        commands = event.get('commands', [])

        for cmd in commands:
            cmd_lower = cmd.lower()

            for pattern_name, pattern in self.ssh_patterns.items():
                if pattern.search(cmd):
                    report.behaviors.append(pattern_name)

            if any(word in cmd_lower for word in ['wget', 'curl', 'tftp']):
                report.behaviors.append('download_malware')
                report.attack_stages.append('execution')
                report.suspicious_commands.append(cmd)

            if any(word in cmd_lower for word in ['nc', 'netcat', 'bash -i', '/dev/tcp']):
                report.behaviors.append('reverse_shell')
                report.attack_stages.append('persistence')
                report.suspicious_commands.append(cmd)

            if 'crontab' in cmd_lower or 'systemctl' in cmd_lower:
                report.behaviors.append('persistence_mechanism')
                report.attack_stages.append('persistence')
                report.suspicious_commands.append(cmd)

            if any(word in cmd_lower for word in ['rm -rf', 'dd if=/dev/zero']):
                report.behaviors.append('destructive_commands')
                report.attack_stages.append('impact')
                report.suspicious_commands.append(cmd)

        auth_attempts = event.get('auth_attempts', [])
        if auth_attempts:
            report.usernames_attempted = [a.get('username') for a in auth_attempts]
            report.passwords_attempted = [a.get('password') for a in auth_attempts]

            if len(auth_attempts) > 10:
                report.behaviors.append('ssh_brute_force')
                report.attack_stages.append('initial_access')

    async def _analyze_web_behavior(self, event: Dict[str, Any], report: ForensicReport) -> None:
        """Analyze web attack behavior."""
        requests = event.get('requests', [])

        for req in requests:
            url = req.get('url', '')
            method = req.get('method', '')
            body = req.get('body', '')

            full_request = f"{url} {body}".lower()

            for pattern in self.sql_patterns:
                if pattern.search(full_request):
                    report.behaviors.append('sql_injection')
                    report.attack_stages.append('initial_access')
                    break

            xss_patterns = [
                r'<script[^>]*>.*?</script>',
                r'javascript:',
                r'onerror\s*=',
                r'onclick\s*=',
                r'<iframe'
            ]
            for pattern in xss_patterns:
                if re.search(pattern, full_request, re.IGNORECASE):
                    report.behaviors.append('xss_attack')
                    report.attack_stages.append('initial_access')
                    break

            cmd_injection_patterns = [
                r';\s*(cat|ls|id|whoami|pwd)',
                r'\|\s*(cat|ls|id|whoami)',
                r'`.*`',
                r'\$\(.*\)'
            ]
            for pattern in cmd_injection_patterns:
                if re.search(pattern, full_request):
                    report.behaviors.append('command_injection')
                    report.attack_stages.append('execution')
                    break

            if '../' in url or '..\\' in url:
                report.behaviors.append('path_traversal')
                report.attack_stages.append('discovery')

            if method == 'POST' and 'upload' in url:
                report.behaviors.append('file_upload')
                report.attack_stages.append('execution')

            auth_bypass_patterns = [
                r"'\s*or\s*'1'\s*=\s*'1",
                r"'\s*or\s*1\s*=\s*1",
                r"admin'\s*--",
                r"' union select"
            ]
            for pattern in auth_bypass_patterns:
                if re.search(pattern, full_request, re.IGNORECASE):
                    report.behaviors.append('auth_bypass')
                    report.attack_stages.append('privilege_escalation')
                    break

    async def _analyze_database_behavior(self, event: Dict[str, Any], report: ForensicReport) -> None:
        """Analyze database attack behavior."""
        queries = event.get('queries', [])

        for query in queries:
            query_lower = query.lower()

            if 'select' in query_lower:
                sensitive_tables = ['customers', 'users', 'credit_card', 'api_credentials']
                if any(table in query_lower for table in sensitive_tables):
                    report.behaviors.append('data_exfiltration')
                    report.attack_stages.append('exfiltration')

                if 'api_credentials' in query_lower or 'ssh_keys' in query_lower:
                    report.behaviors.append('honeytoken_access')
                    report.attack_stages.append('collection')

            if any(word in query_lower for word in ['grant', 'alter user', 'create user']):
                report.behaviors.append('privilege_escalation')
                report.attack_stages.append('privilege_escalation')

            if any(word in query_lower for word in ['drop table', 'truncate', 'delete from']):
                report.behaviors.append('data_destruction')
                report.attack_stages.append('impact')

            if '--' in query or '/*' in query or 'union select' in query_lower:
                report.behaviors.append('sql_injection')
                report.attack_stages.append('initial_access')

    async def _analyze_payload(self, event: Dict[str, Any], report: ForensicReport) -> None:
        """Analyze payloads for malware and exploits."""
        files = event.get('uploaded_files', [])
        for file_info in files:
            file_hash = file_info.get('sha256')
            if file_hash:
                report.file_hashes.append(file_hash)

                if file_hash in self.malware_signatures:
                    report.malware_detected = True
                    report.malware_family = self.malware_signatures[file_hash]
                    report.behaviors.append('malware_upload')
                    report.attack_stages.append('execution')

        payload = event.get('payload', '')
        if payload:
            for cve, signature in self.cve_database.items():
                if signature in payload:
                    report.exploit_cves.append(cve)
                    report.behaviors.append('exploit_attempt')
                    report.attack_stages.append('exploitation')

    async def _analyze_credentials(self, event: Dict[str, Any], report: ForensicReport) -> None:
        """Analyze credential usage and compromise."""
        if event.get('auth_success', False):
            report.credentials_compromised = True
            report.behaviors.append('successful_authentication')
            report.attack_stages.append('initial_access')

        commands = event.get('commands', [])
        cred_dump_patterns = [
            'mimikatz', '/etc/shadow', '/etc/passwd',
            'sam', 'lsass', 'hashdump'
        ]
        for cmd in commands:
            if any(pattern in cmd.lower() for pattern in cred_dump_patterns):
                report.behaviors.append('credential_dumping')
                report.attack_stages.append('credential_access')
                report.suspicious_commands.append(cmd)

    async def _analyze_temporal_patterns(self, event: Dict[str, Any], report: ForensicReport) -> None:
        """Analyze timing patterns to detect automation."""
        requests = event.get('requests', [])
        if len(requests) > 5:
            timestamps = [r.get('timestamp') for r in requests if r.get('timestamp')]
            if len(timestamps) > 1:
                intervals = []
                for i in range(1, len(timestamps)):
                    interval = (timestamps[i] - timestamps[i-1]).total_seconds()
                    intervals.append(interval)

                if intervals:
                    avg_interval = sum(intervals) / len(intervals)
                    variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)

                    if variance < 0.1:
                        report.is_automated = True
                        report.behaviors.append('automated_attack')

                    report.request_rate = 1.0 / avg_interval if avg_interval > 0 else 0.0

        report.attack_duration = event.get('session_duration', 0.0)
