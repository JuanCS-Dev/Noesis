"""
Shutdown Methods for Kill Switch.

Different levels of shutdown operations.
"""

from __future__ import annotations

import logging
import os
import signal
import subprocess
import time
from typing import List

from .models import ComponentType, KillTarget

logger = logging.getLogger(__name__)


class ShutdownMixin:
    """Mixin providing shutdown method implementations."""

    def _graceful_shutdown(self, targets: List[KillTarget]) -> List[str]:
        """Graceful shutdown with cleanup."""
        killed = []

        for target in targets:
            try:
                if target.component_type == ComponentType.CONTAINER:
                    # Docker stop (graceful)
                    cmd = ["docker", "stop", "-t", "30", target.id]
                    subprocess.run(cmd, capture_output=True, timeout=35, check=False)

                elif target.component_type == ComponentType.PROCESS:
                    # SIGTERM
                    os.kill(int(target.id), signal.SIGTERM)
                    time.sleep(2)  # Give time to cleanup

                elif target.component_type == ComponentType.SERVICE:
                    # Systemctl stop
                    cmd = ["systemctl", "stop", target.id]
                    subprocess.run(cmd, capture_output=True, timeout=30, check=False)

                killed.append(target.id)
                logger.info("Gracefully stopped: %s", target.name)

            except Exception as e:
                logger.error("Failed to gracefully stop %s: %s", target.name, e)

        return killed

    def _immediate_shutdown(self, targets: List[KillTarget]) -> List[str]:
        """Immediate shutdown, minimal cleanup."""
        killed = []

        for target in targets:
            try:
                if target.component_type == ComponentType.CONTAINER:
                    # Docker kill
                    cmd = ["docker", "kill", target.id]
                    subprocess.run(cmd, capture_output=True, timeout=5, check=False)

                elif target.component_type == ComponentType.PROCESS:
                    # SIGKILL
                    os.kill(int(target.id), signal.SIGKILL)

                elif target.component_type == ComponentType.NETWORK:
                    # Drop network
                    cmd = ["docker", "network", "disconnect", "-f", target.id]
                    subprocess.run(cmd, capture_output=True, timeout=5, check=False)

                killed.append(target.id)
                logger.warning("Immediately killed: %s", target.name)

            except Exception as e:
                logger.error("Failed to kill %s: %s", target.name, e)

        return killed

    def _emergency_shutdown(self, targets: List[KillTarget]) -> List[str]:
        """Emergency shutdown - instant kill all."""
        killed = []

        # Kill all targets in parallel for speed
        kill_commands = []

        for target in targets:
            if target.kill_command:
                kill_commands.append(target.kill_command)
            elif target.component_type == ComponentType.CONTAINER:
                kill_commands.append(f"docker kill {target.id}")
            elif target.component_type == ComponentType.PROCESS:
                kill_commands.append(f"kill -9 {target.id}")

        # Execute all kills in parallel
        processes = []
        for cmd in kill_commands:
            p = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            processes.append(p)

        # Wait for completion (max 5 seconds)
        for p in processes:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()

        # Mark all as killed (optimistic)
        killed = [t.id for t in targets]

        logger.critical("EMERGENCY KILL completed: %d targets", len(killed))
        return killed

    def _nuclear_shutdown(self, targets: List[KillTarget]) -> List[str]:
        """
        NUCLEAR OPTION - Destroy everything including data.

        USE ONLY IN EXTREME CONTAINMENT BREACH.
        """
        logger.critical("NUCLEAR SHUTDOWN INITIATED - DESTROYING ALL DATA")

        killed = []

        try:
            # 1. Kill all containers
            subprocess.run(
                "docker kill $(docker ps -q)",
                shell=True,
                capture_output=True,
                timeout=5,
                check=False,
            )

            # 2. Remove all containers
            subprocess.run(
                "docker rm -f $(docker ps -aq)",
                shell=True,
                capture_output=True,
                timeout=5,
                check=False,
            )

            # 3. Delete all networks
            subprocess.run(
                "docker network prune -f",
                shell=True,
                capture_output=True,
                timeout=5,
                check=False,
            )

            # 4. Delete all volumes (DATA LOSS!)
            if os.getenv("ALLOW_NUCLEAR_DATA_LOSS", "false").lower() == "true":
                subprocess.run(
                    "docker volume prune -f",
                    shell=True,
                    capture_output=True,
                    timeout=5,
                    check=False,
                )

                # Delete honeypot data
                honeypot_dirs = [
                    "/var/lib/reactive_fabric/honeypots",
                    "/var/log/reactive_fabric",
                    "/tmp/reactive_fabric",
                ]

                for dir_path in honeypot_dirs:
                    try:
                        subprocess.run(
                            f"rm -rf {dir_path}",
                            shell=True,
                            capture_output=True,
                            timeout=5,
                            check=False,
                        )
                    except Exception:
                        pass

            # 5. Kill all processes matching pattern
            subprocess.run(
                "pkill -9 -f reactive_fabric",
                shell=True,
                capture_output=True,
                timeout=5,
                check=False,
            )

            killed = [t.id for t in targets]
            logger.critical("NUCLEAR SHUTDOWN COMPLETE - System destroyed")

        except Exception as e:
            logger.error("Nuclear shutdown error: %s", e)

        return killed
