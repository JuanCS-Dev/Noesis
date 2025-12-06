"""
Alert System for PostgreSQL Honeypot.

Honeytoken alerts and query analysis.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class AlertMixin:
    """Mixin providing alert capabilities."""

    log_path: Path
    _running: bool
    honeypot_id: str
    query_count: int
    suspicious_queries: List[Dict[str, Any]]
    honeytokens_planted: List[Dict[str, Any]]

    async def _trigger_honeytoken_alert(self, query: str) -> None:
        """Trigger critical alert when honeytoken is accessed."""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "honeypot_id": self.honeypot_id,
            "alert_type": "HONEYTOKEN_ACCESSED",
            "severity": "CRITICAL",
            "query": query,
            "honeytokens_exposed": [
                token
                for token in self.honeytokens_planted
                if token["identifier"].lower() in query.lower()
            ],
        }

        # Save alert
        alert_file = (
            self.log_path
            / "alerts"
            / f"honeytoken_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        alert_file.parent.mkdir(exist_ok=True)

        with open(alert_file, "w") as f:
            json.dump(alert, f, indent=2)

        logger.critical("HONEYTOKEN ALERT saved: %s", alert_file)

    async def _analyze_queries(self) -> None:
        """Periodic analysis of query patterns."""
        while self._running:
            await asyncio.sleep(300)  # Every 5 minutes

            if self.suspicious_queries:
                logger.info(
                    "Analyzed %d suspicious queries", len(self.suspicious_queries)
                )

                # Generate report
                report_path = (
                    self.log_path
                    / "reports"
                    / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
                )
                report_path.parent.mkdir(exist_ok=True)

                with open(report_path, "w") as f:
                    json.dump(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "total_queries": self.query_count,
                            "suspicious_queries": len(self.suspicious_queries),
                            "recent_suspicious": self.suspicious_queries[-10:],
                        },
                        f,
                        indent=2,
                        default=str,
                    )

    def get_honeytoken_status(self) -> Dict[str, Any]:
        """Get status of planted honeytokens."""
        return {
            "total_planted": len(self.honeytokens_planted),
            "honeytokens": self.honeytokens_planted,
            "last_check": datetime.now().isoformat(),
        }
