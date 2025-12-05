"""
Log Monitoring for PostgreSQL Honeypot.

Real-time log analysis and query handling.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class LogMonitorMixin:
    """Mixin providing log monitoring capabilities."""

    log_path: Path
    _running: bool
    query_count: int
    suspicious_queries: List[Dict[str, Any]]
    honeytokens_planted: List[Dict[str, Any]]

    async def _trigger_honeytoken_alert(self, query: str) -> None:
        """Trigger alert (implemented in alerts mixin)."""
        raise NotImplementedError

    async def _monitor_postgres_logs(self) -> None:
        """Monitor PostgreSQL logs in real-time."""
        log_file = self.log_path / "logs" / "postgresql.log"

        # Wait for log file
        while not log_file.exists() and self._running:
            await asyncio.sleep(5)

        if not self._running:
            return

        cmd = ["tail", "-f", str(log_file)]
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

                    log_entry = line.decode().strip()
                    await self._process_log_entry(log_entry)

            except Exception as e:
                logger.error("Error monitoring PostgreSQL logs: %s", e)

        process.terminate()

    async def _process_log_entry(self, log_entry: str) -> None:
        """Process a PostgreSQL log entry."""
        # Look for connections
        if "connection received" in log_entry or "connection authorized" in log_entry:
            await self._handle_connection(log_entry)

        # Look for queries
        elif "statement:" in log_entry or "execute" in log_entry:
            await self._handle_query(log_entry)

        # Look for errors (SQL injection attempts often cause errors)
        elif "ERROR:" in log_entry or "FATAL:" in log_entry:
            await self._handle_error(log_entry)

    async def _handle_connection(self, log_entry: str) -> None:
        """Handle new database connection."""
        self.query_count += 1
        logger.info("New PostgreSQL connection detected: %s", log_entry[:100])

    async def _handle_query(self, log_entry: str) -> None:
        """Handle SQL query execution."""
        # Check for suspicious patterns
        suspicious_patterns = [
            "api_credentials",
            "ssh_keys",
            "password_hash",
            "ssn",
            "credit_card",
            "UNION SELECT",
            "DROP TABLE",
            "pg_sleep",
            "pg_read_file",
            "COPY.*FROM PROGRAM",
        ]

        is_suspicious = any(
            pattern.lower() in log_entry.lower() for pattern in suspicious_patterns
        )

        if is_suspicious:
            self.suspicious_queries.append({
                "timestamp": datetime.now(),
                "query": log_entry,
                "alert_level": "HIGH",
            })

            logger.warning("SUSPICIOUS QUERY detected: %s", log_entry[:200])

            # Check if honeytoken was accessed
            honeytoken_tables = ["api_credentials", "ssh_keys", "internal_endpoints"]
            if any(token in log_entry for token in honeytoken_tables):
                logger.critical("HONEYTOKEN TABLE ACCESSED!")
                await self._trigger_honeytoken_alert(log_entry)

    async def _handle_error(self, log_entry: str) -> None:
        """Handle database errors (often from SQL injection)."""
        logger.info("Database error logged: %s", log_entry[:100])

        # SQL injection attempts often cause syntax errors
        if "syntax error" in log_entry.lower():
            logger.warning("Potential SQL injection attempt detected")
