"""
Database Loaders for Attribution Engine.

Threat actor profiles, TTP signatures, and infrastructure intelligence.
"""

from __future__ import annotations

from typing import Any, Dict


def load_threat_actor_database() -> Dict[str, Dict[str, Any]]:
    """Load threat actor profiles."""
    return {
        'APT28': {
            'type': 'nation_state',
            'motivation': 'espionage',
            'typical_sophistication': 8.5,
            'description': 'Russian military intelligence (GRU)',
            'aliases': ['Fancy Bear', 'Sofacy', 'Pawn Storm']
        },
        'APT29': {
            'type': 'nation_state',
            'motivation': 'espionage',
            'typical_sophistication': 9.0,
            'description': 'Russian foreign intelligence (SVR)',
            'aliases': ['Cozy Bear', 'The Dukes']
        },
        'Lazarus Group': {
            'type': 'nation_state',
            'motivation': 'financial',
            'typical_sophistication': 8.0,
            'description': 'North Korean state-sponsored',
            'aliases': ['Hidden Cobra', 'Guardians of Peace']
        },
        'APT41': {
            'type': 'nation_state',
            'motivation': 'espionage',
            'typical_sophistication': 8.5,
            'description': 'Chinese state-sponsored',
            'aliases': ['Double Dragon', 'Barium']
        },
        'FIN7': {
            'type': 'criminal',
            'motivation': 'financial',
            'typical_sophistication': 7.5,
            'description': 'Cybercriminal group targeting financial sector',
            'aliases': ['Carbanak']
        },
        'Anonymous': {
            'type': 'hacktivist',
            'motivation': 'disruption',
            'typical_sophistication': 5.0,
            'description': 'Decentralized hacktivist collective',
            'aliases': []
        },
        'Script Kiddie': {
            'type': 'script_kiddie',
            'motivation': 'testing',
            'typical_sophistication': 2.0,
            'description': 'Unskilled attacker using existing tools',
            'aliases': []
        },
        'Opportunistic Scanner': {
            'type': 'automated',
            'motivation': 'discovery',
            'typical_sophistication': 1.0,
            'description': 'Automated scanning and exploitation',
            'aliases': []
        }
    }


def build_ttp_signatures() -> Dict[str, Dict[str, Any]]:
    """Build TTP signatures for each actor."""
    return {
        'APT28': {
            'ttps': [
                'spearphishing', 'credential_dumping', 'lateral_movement',
                'persistence', 'defense_evasion', 'data_exfiltration'
            ]
        },
        'APT29': {
            'ttps': [
                'supply_chain_compromise', 'privilege_escalation',
                'lateral_movement', 'persistence', 'data_exfiltration',
                'defense_evasion', 'obfuscation'
            ]
        },
        'Lazarus Group': {
            'ttps': [
                'spearphishing', 'watering_hole', 'malware_upload',
                'destructive_commands', 'data_destruction', 'ransomware'
            ]
        },
        'FIN7': {
            'ttps': [
                'sql_injection', 'credential_dumping', 'data_exfiltration',
                'point_of_sale_malware', 'financial_data_theft'
            ]
        },
        'Anonymous': {
            'ttps': [
                'ddos', 'sql_injection', 'xss_attack', 'defacement',
                'data_leak', 'doxxing'
            ]
        },
        'Script Kiddie': {
            'ttps': [
                'ssh_brute_force', 'sql_injection', 'xss_attack',
                'scanner_user_agent', 'automated_attack'
            ]
        },
        'Opportunistic Scanner': {
            'ttps': [
                'reconnaissance', 'scanner_user_agent', 'automated_attack',
                'ssh_brute_force', 'exploit_attempt'
            ]
        }
    }


def build_tool_signatures() -> Dict[str, Dict[str, Any]]:
    """Build tool signatures for each actor."""
    return {
        'APT28': {
            'tools': ['X-Agent', 'Sofacy', 'Komplex', 'XTunnel', 'mimikatz']
        },
        'APT29': {
            'tools': ['WellMess', 'WellMail', 'Cobalt Strike', 'PowerShell Empire']
        },
        'Lazarus Group': {
            'tools': ['Destover', 'Volgmer', 'Duuzer', 'Trojan.Manuscrypt']
        },
        'FIN7': {
            'tools': ['Carbanak', 'Cobalt Strike', 'DNSMessenger', 'GRIFFON']
        },
        'Anonymous': {
            'tools': ['LOIC', 'HOIC', 'sqlmap', 'havij']
        },
        'Script Kiddie': {
            'tools': ['metasploit', 'sqlmap', 'nikto', 'nmap', 'hydra']
        },
        'Opportunistic Scanner': {
            'tools': ['masscan', 'shodan', 'nmap', 'zmap']
        }
    }


def load_infrastructure_database() -> Dict[str, Dict[str, Any]]:
    """Load infrastructure intelligence."""
    return {
        'APT28': {
            'ip_ranges': ['185.86.148.0/24', '193.169.244.0/24'],
            'asns': ['AS44812'],
            'hosting_providers': ['serveroid.com', 'rackservice.org']
        },
        'APT29': {
            'ip_ranges': ['45.32.0.0/16', '185.231.155.0/24'],
            'asns': ['AS64425'],
            'hosting_providers': ['vultr.com']
        },
        'Lazarus Group': {
            'ip_ranges': ['175.45.176.0/24'],
            'asns': ['AS4766'],
            'hosting_providers': []
        }
    }
