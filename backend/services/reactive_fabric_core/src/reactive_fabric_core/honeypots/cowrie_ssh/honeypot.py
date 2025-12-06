"""
Main Cowrie SSH Honeypot Class.

High-interaction SSH/Telnet honeypot.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Set

from ..base_honeypot import BaseHoneypot, HoneypotType
from .command_analysis import CommandAnalysisMixin
from .config import ConfigMixin
from .event_handlers import EventHandlerMixin
from .file_handlers import FileHandlerMixin
from .log_monitor import LogMonitorMixin
from .reporting import ReportingMixin

logger = logging.getLogger(__name__)


class CowrieSSHHoneypot(
    ConfigMixin,
    LogMonitorMixin,
    CommandAnalysisMixin,
    EventHandlerMixin,
    FileHandlerMixin,
    ReportingMixin,
    BaseHoneypot,
):
    """
    Cowrie SSH/Telnet Honeypot.

    Captures brute force attacks, commands, and uploaded malware.
    """

    def __init__(
        self,
        honeypot_id: str = "cowrie_ssh",
        ssh_port: int = 2222,
        telnet_port: int = 2223,
        layer: int = 3,
    ) -> None:
        """
        Initialize Cowrie SSH honeypot.

        Args:
            honeypot_id: Unique identifier
            ssh_port: SSH port to listen on
            telnet_port: Telnet port to listen on
            layer: Network layer
        """
        super().__init__(
            honeypot_id=honeypot_id,
            honeypot_type=HoneypotType.SSH,
            port=ssh_port,
            layer=layer,
        )

        self.telnet_port = telnet_port
        self.cowrie_config = self._generate_config()

        # Attack patterns
        self.brute_force_attempts: Dict[str, List[Dict[str, Any]]] = {}
        self.known_malware_hashes: Set[str] = set()

    def get_docker_config(self) -> Dict[str, Any]:
        """Get Docker configuration for Cowrie."""
        return {
            "image": "cowrie/cowrie:latest",
            "internal_port": 2222,
            "hostname": "production-server-01",
            "environment": {
                "COWRIE_SSH_ENABLED": "yes",
                "COWRIE_TELNET_ENABLED": "yes",
                "COWRIE_OUTPUT_JSON_ENABLED": "yes",
                "COWRIE_HOSTNAME": self.cowrie_config["honeypot"]["hostname"],
                "COWRIE_KERNEL_VERSION": self.cowrie_config["honeypot"][
                    "kernel_version"
                ],
            },
            "volumes": [
                f"{self.log_path}:/cowrie/cowrie-logs",
                f"{self.log_path}/downloads:/cowrie/downloads",
                f"{self.log_path}/tty:/cowrie/tty",
                f"{self.log_path}/keys:/cowrie/etc/keys",
            ],
            "memory": "1g",
            "cpus": "1.0",
        }

    async def start(self) -> bool:
        """Start Cowrie honeypot."""
        logger.info("Starting Cowrie SSH honeypot on port %d", self.port)

        # Create necessary directories
        for dir_name in ["downloads", "tty", "keys", "json"]:
            (self.log_path / dir_name).mkdir(parents=True, exist_ok=True)

        # Deploy container
        success = await self.deploy()

        if success:
            # Start log monitoring
            asyncio.create_task(self._monitor_cowrie_logs())

        return success

    async def stop(self) -> bool:
        """Stop Cowrie honeypot."""
        logger.info("Stopping Cowrie SSH honeypot")
        await self.shutdown()
        return True
