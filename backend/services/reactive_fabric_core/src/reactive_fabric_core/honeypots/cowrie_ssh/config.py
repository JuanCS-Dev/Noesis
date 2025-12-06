"""
Configuration for Cowrie SSH Honeypot.

Cowrie honeypot configuration generation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


class ConfigMixin:
    """Mixin providing configuration generation."""

    port: int
    telnet_port: int
    log_path: Path

    def _generate_config(self) -> Dict[str, Any]:
        """Generate Cowrie configuration."""
        return {
            "ssh": {
                "enabled": True,
                "port": self.port,
                "version": "SSH-2.0-OpenSSH_7.4",
                "auth_methods": ["password", "publickey"],
                "max_auth_tries": 6,
            },
            "telnet": {
                "enabled": True,
                "port": self.telnet_port,
            },
            "honeypot": {
                "hostname": "production-server-01",
                "kernel_version": "4.15.0-142-generic",
                "kernel_build": "#146-Ubuntu SMP Tue Jun 29 14:33:35 UTC 2021",
                "operating_system": "Ubuntu 18.04.5 LTS",
                "architecture": "x86_64",
            },
            "output": {
                "json": {
                    "enabled": True,
                    "logfile": str(self.log_path / "cowrie.json"),
                },
                "tty": {
                    "enabled": True,
                    "path": str(self.log_path / "tty"),
                },
                "downloads": {
                    "enabled": True,
                    "path": str(self.log_path / "downloads"),
                },
            },
            "shell": {
                "filesystem": "/opt/cowrie/share/cowrie/fs.pickle",
                "processes": "/opt/cowrie/share/cowrie/cmdoutput.json",
                "exec_enabled": True,
                "download_limit": 10485760,  # 10MB
            },
        }
