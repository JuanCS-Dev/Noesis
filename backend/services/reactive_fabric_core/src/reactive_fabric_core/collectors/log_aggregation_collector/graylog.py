"""
Graylog Backend for Log Aggregation Collector.

Graylog log collection and parsing.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional

import aiohttp

from ..base_collector import CollectedEvent
from .models import LogAggregationConfig, SecurityEventPattern

logger = logging.getLogger(__name__)


class GraylogMixin:
    """Mixin providing Graylog collection capabilities."""

    config: LogAggregationConfig
    session: Optional[aiohttp.ClientSession]
    security_patterns: List[SecurityEventPattern]
    metrics: Any

    async def _collect_graylog(
        self,
        from_time: datetime,
        to_time: datetime,
    ) -> AsyncIterator[CollectedEvent]:
        """Collect logs from Graylog."""
        if not self.session:
            return

        # Build Graylog query
        query_patterns = " OR ".join([
            pattern
            for security_pattern in self.security_patterns
            for pattern in security_pattern.patterns
        ])

        query_params = {
            "query": query_patterns,
            "from": from_time.isoformat(),
            "to": to_time.isoformat(),
            "limit": self.config.max_results_per_query,
        }

        url = (
            f"http://{self.config.host}:{self.config.port}"
            "/api/search/universal/relative"
        )

        try:
            async with self.session.get(url, params=query_params) as response:
                if response.status != 200:
                    return

                data = await response.json()
                for message in data.get("messages", []):
                    event = await self._parse_graylog_message(message)
                    if event:
                        yield event

        except Exception as e:
            logger.error("Error collecting from Graylog: %s", e)

    async def _parse_graylog_message(
        self,
        message: Dict[str, Any],
    ) -> Optional[CollectedEvent]:
        """Parse Graylog message into CollectedEvent."""
        try:
            msg_text = message.get("message", {}).get("message", "")

            # Identify matching security pattern
            matched_pattern = None
            for pattern in self.security_patterns:
                if any(p.lower() in msg_text.lower() for p in pattern.patterns):
                    matched_pattern = pattern
                    break

            if not matched_pattern:
                return None

            return CollectedEvent(
                collector_type="LogAggregation",
                source=f"graylog:{message.get('index', 'unknown')}",
                severity=matched_pattern.severity,
                raw_data=message.get("message", {}),
                parsed_data={
                    "pattern_name": matched_pattern.name,
                    "stream_ids": message.get("stream_ids", []),
                    "mitre_techniques": matched_pattern.mitre_techniques,
                },
                tags=[
                    f"pattern:{matched_pattern.name}",
                    "backend:graylog",
                    *[f"mitre:{t}" for t in matched_pattern.mitre_techniques],
                ],
            )

        except Exception as e:
            logger.error("Error parsing Graylog message: %s", e)
            return None
