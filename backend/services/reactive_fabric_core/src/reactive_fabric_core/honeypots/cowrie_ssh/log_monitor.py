"""
Log Monitoring for Cowrie SSH Honeypot.

Real-time log processing.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class LogMonitorMixin:
    """Mixin providing log monitoring capabilities."""

    log_path: Path
    _running: bool

    async def _process_cowrie_event(self, event: Dict[str, Any]) -> None:
        """Process a single Cowrie event (implemented in event handlers)."""
        raise NotImplementedError

    async def _process_logs(self) -> None:
        """Process Cowrie JSON logs for attacks."""
        json_log = self.log_path / "cowrie.json"

        if not json_log.exists():
            return

        try:
            # Read new lines since last check
            with open(json_log) as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        await self._process_cowrie_event(event)
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error("Error processing Cowrie logs: %s", e)

    async def _monitor_cowrie_logs(self) -> None:
        """Monitor Cowrie logs in real-time."""
        json_log = self.log_path / "cowrie.json"

        # Wait for log file to be created
        while not json_log.exists() and self._running:
            await asyncio.sleep(5)

        # Tail the log file
        cmd = ["tail", "-f", str(json_log)]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        while self._running:
            try:
                if process.stdout:
                    line = await process.stdout.readline()
                    if not line:
                        break

                    event = json.loads(line.decode().strip())
                    await self._process_cowrie_event(event)

            except Exception as e:
                logger.error("Error monitoring Cowrie logs: %s", e)

        process.terminate()
