"""Models for HCL orchestrator module."""

from __future__ import annotations

from typing import Any


class HCLConfig:
    """Configuration for HCL orchestrator."""

    def __init__(
        self,
        dry_run_mode: bool = True,
        loop_interval_seconds: int = 30,
        db_url: str = "postgresql://localhost/vertice",
    ) -> None:
        """Initialize HCL config."""
        self.dry_run_mode = dry_run_mode
        self.loop_interval = loop_interval_seconds
        self.db_url = db_url
