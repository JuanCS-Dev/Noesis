"""
Main PostgreSQL Honeypot Class.

Database honeypot with realistic fake data and honeytokens.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List

from ..base_honeypot import BaseHoneypot, HoneypotType
from .alerts import AlertMixin
from .fake_data import FakeDataMixin
from .honeytokens import HoneytokenMixin
from .log_monitor import LogMonitorMixin
from .schema import SchemaMixin

logger = logging.getLogger(__name__)


class PostgreSQLHoneypot(
    SchemaMixin,
    FakeDataMixin,
    HoneytokenMixin,
    LogMonitorMixin,
    AlertMixin,
    BaseHoneypot,
):
    """
    PostgreSQL Database Honeypot.

    Contains realistic fake data with planted honeytokens.
    """

    def __init__(
        self,
        honeypot_id: str = "postgres_db",
        port: int = 5433,
        layer: int = 3,
    ) -> None:
        """
        Initialize PostgreSQL honeypot.

        Args:
            honeypot_id: Unique identifier
            port: PostgreSQL port to listen on
            layer: Network layer
        """
        super().__init__(
            honeypot_id=honeypot_id,
            honeypot_type=HoneypotType.DATABASE,
            port=port,
            layer=layer,
        )

        self.db_config = self._generate_config()
        self.honeytokens_planted: List[Dict[str, Any]] = []

        # Query tracking
        self.suspicious_queries: List[Dict[str, Any]] = []
        self.query_count = 0

    def _generate_config(self) -> Dict[str, Any]:
        """Generate PostgreSQL configuration."""
        return {
            "database": "production_backup",
            "user": "backup_user",
            "password": "Backup2024!",  # Weak but realistic
            "max_connections": 100,
            "shared_buffers": "256MB",
            "log_statement": "all",  # Log everything
            "log_connections": True,
            "log_disconnections": True,
        }

    def get_docker_config(self) -> Dict[str, Any]:
        """Get Docker configuration for PostgreSQL."""
        return {
            "image": "postgres:14",
            "internal_port": 5432,
            "hostname": "db-backup-01",
            "environment": {
                "POSTGRES_DB": self.db_config["database"],
                "POSTGRES_USER": self.db_config["user"],
                "POSTGRES_PASSWORD": self.db_config["password"],
                "POSTGRES_INITDB_ARGS": "-c shared_buffers=256MB",
                "PGDATA": "/var/lib/postgresql/data/pgdata",
            },
            "volumes": [
                f"{self.log_path}/data:/var/lib/postgresql/data",
                f"{self.log_path}/logs:/var/log/postgresql",
                f"{self.log_path}/init:/docker-entrypoint-initdb.d",
            ],
            "memory": "2g",
            "cpus": "1.5",
            "command": [
                "postgres",
                "-c",
                "log_statement=all",
                "-c",
                "log_connections=on",
                "-c",
                "log_disconnections=on",
                "-c",
                "log_duration=on",
            ],
        }

    async def start(self) -> bool:
        """Start PostgreSQL honeypot."""
        logger.info("Starting PostgreSQL honeypot on port %d", self.port)

        # Create necessary directories
        for dir_name in ["data", "logs", "init", "backups"]:
            (self.log_path / dir_name).mkdir(parents=True, exist_ok=True)

        # Generate initialization SQL with fake data
        await self._generate_init_sql()

        # Deploy container
        success = await self.deploy()

        if success:
            # Wait for PostgreSQL to be ready
            await asyncio.sleep(10)

            # Start log monitoring
            asyncio.create_task(self._monitor_postgres_logs())

            # Start query analysis
            asyncio.create_task(self._analyze_queries())

        return success

    async def stop(self) -> bool:
        """Stop PostgreSQL honeypot."""
        logger.info("Stopping PostgreSQL honeypot")
        await self.shutdown()
        return True

    async def _generate_init_sql(self) -> None:
        """Generate SQL initialization script with fake data."""
        init_sql_path = self.log_path / "init" / "01-init.sql"

        sql_content = self._build_database_schema()
        sql_content += self._build_fake_customer_data()
        sql_content += self._build_honeytoken_tables()
        sql_content += self._build_audit_triggers()

        with open(init_sql_path, "w") as f:
            f.write(sql_content)

        logger.info("Generated initialization SQL with fake data and honeytokens")

    async def _process_logs(self) -> None:
        """Process PostgreSQL logs for suspicious activity."""
        pass  # Implemented in monitor task
