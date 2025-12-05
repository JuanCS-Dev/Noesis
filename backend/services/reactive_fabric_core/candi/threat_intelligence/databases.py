"""
Database Loaders for Threat Intelligence.

IOC, tool, exploit, and campaign databases.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict


def load_ioc_database() -> Dict[str, Dict[str, Any]]:
    """Load local IOC database."""
    return {
        'ip:185.86.148.10': {
            'reputation': 'malicious',
            'tags': ['apt28', 'russia', 'military'],
            'first_seen': datetime.now() - timedelta(days=180),
            'last_seen': datetime.now() - timedelta(days=5),
            'related_iocs': ['ip:185.86.148.11', 'ip:185.86.148.12'],
        },
        'ip:45.32.10.15': {
            'reputation': 'suspicious',
            'tags': ['apt29', 'russia', 'intelligence'],
            'first_seen': datetime.now() - timedelta(days=90),
            'last_seen': datetime.now() - timedelta(days=2),
            'related_iocs': ['domain:example-c2.com'],
        },
        'sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855': {
            'reputation': 'malicious',
            'tags': ['mirai', 'botnet', 'iot'],
            'first_seen': datetime.now() - timedelta(days=365),
            'last_seen': datetime.now() - timedelta(days=10),
            'related_iocs': [],
        },
    }


def load_tool_database() -> Dict[str, Dict[str, Any]]:
    """Load tool/malware database."""
    return {
        'mimikatz': {
            'type': 'credential_dumper',
            'tags': ['credential_access', 'post_exploitation'],
            'severity': 'high',
        },
        'cobalt strike': {
            'type': 'c2_framework',
            'tags': ['apt', 'command_and_control', 'post_exploitation'],
            'severity': 'critical',
        },
        'metasploit': {
            'type': 'exploit_framework',
            'tags': ['exploitation', 'penetration_testing'],
            'severity': 'medium',
        },
        'nmap': {
            'type': 'scanner',
            'tags': ['reconnaissance', 'discovery'],
            'severity': 'low',
        },
        'sqlmap': {
            'type': 'sql_injection_tool',
            'tags': ['web_attack', 'sql_injection'],
            'severity': 'medium',
        },
        'mirai': {
            'type': 'botnet',
            'tags': ['iot', 'ddos', 'malware'],
            'severity': 'high',
        },
        'empire': {
            'type': 'c2_framework',
            'tags': ['post_exploitation', 'powershell'],
            'severity': 'high',
        },
    }


def load_exploit_database() -> Dict[str, Dict[str, Any]]:
    """Load exploit/CVE database."""
    return {
        'CVE-2021-44228': {
            'name': 'Log4Shell',
            'severity': 'critical',
            'tags': ['java', 'rce', 'widespread'],
            'description': 'Apache Log4j2 RCE vulnerability',
        },
        'CVE-2017-5638': {
            'name': 'Apache Struts2 RCE',
            'severity': 'critical',
            'tags': ['java', 'rce', 'web'],
            'description': 'Apache Struts2 content-type RCE',
        },
        'CVE-2019-0708': {
            'name': 'BlueKeep',
            'severity': 'critical',
            'tags': ['rdp', 'windows', 'wormable'],
            'description': 'Windows RDP RCE vulnerability',
        },
        'CVE-2020-1472': {
            'name': 'Zerologon',
            'severity': 'critical',
            'tags': ['windows', 'domain_controller', 'privilege_escalation'],
            'description': 'Windows Netlogon privilege escalation',
        },
    }


def load_campaign_database() -> Dict[str, Dict[str, Any]]:
    """Load threat campaign database."""
    return {
        'SolarWinds Supply Chain Attack': {
            'actor': 'APT29',
            'start_date': '2020-03-01',
            'behaviors': [
                'supply_chain_compromise',
                'lateral_movement',
                'credential_dumping',
                'data_exfiltration',
            ],
            'tags': ['apt29', 'supply_chain', 'espionage'],
        },
        'NotPetya Ransomware Campaign': {
            'actor': 'Sandworm',
            'start_date': '2017-06-01',
            'behaviors': [
                'destructive_commands',
                'data_destruction',
                'lateral_movement',
                'credential_dumping',
            ],
            'tags': ['sandworm', 'ransomware', 'destructive'],
        },
        'Hafnium Exchange Server Attacks': {
            'actor': 'Hafnium',
            'start_date': '2021-01-01',
            'behaviors': [
                'exploit_attempt',
                'web_shell',
                'data_exfiltration',
                'lateral_movement',
            ],
            'tags': ['hafnium', 'exchange', 'china'],
        },
        'Emotet Campaign': {
            'actor': 'TA542',
            'start_date': '2014-01-01',
            'behaviors': [
                'spearphishing',
                'malware_upload',
                'credential_dumping',
                'lateral_movement',
                'data_exfiltration',
            ],
            'tags': ['emotet', 'banking_trojan', 'botnet'],
        },
    }
