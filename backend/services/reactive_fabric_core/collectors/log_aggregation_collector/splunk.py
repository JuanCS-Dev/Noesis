"""
Splunk Backend for Log Aggregation Collector.

Splunk log collection and parsing.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional

import aiohttp

from ..base_collector import CollectedEvent
from .models import LogAggregationConfig, SecurityEventPattern

logger = logging.getLogger(__name__)


class SplunkMixin:
    """Mixin providing Splunk collection capabilities."""

    config: LogAggregationConfig
    session: Optional[aiohttp.ClientSession]
    security_patterns: List[SecurityEventPattern]
    metrics: Any

    async def _collect_splunk(
        self,
        from_time: datetime,
        to_time: datetime,
    ) -> AsyncIterator[CollectedEvent]:
        """Collect logs from Splunk."""
        if not self.session:
            return

        # Build Splunk search query
        search_patterns = " OR ".join([
            f'"{pattern}"'
            for security_pattern in self.security_patterns
            for pattern in security_pattern.patterns
        ])

        search_query = (
            f"search earliest={from_time.timestamp()} "
            f"latest={to_time.timestamp()} "
            f"({search_patterns})"
        )

        # Submit search job
        job_url = (
            f"https://{self.config.host}:{self.config.port}/services/search/jobs"
        )
        job_data = {
            "search": search_query,
            "output_mode": "json",
            "max_count": self.config.max_results_per_query,
        }

        try:
            async with self.session.post(job_url, data=job_data) as response:
                if response.status != 201:
                    logger.error(
                        "Failed to create Splunk search job: %s", response.status
                    )
                    return

                job_info = await response.json()
                job_sid = job_info.get("sid")

                if not job_sid:
                    return

                # Wait for job completion and get results
                results_url = (
                    f"https://{self.config.host}:{self.config.port}"
                    f"/services/search/jobs/{job_sid}/results"
                )

                # Poll for job completion
                await asyncio.sleep(2)  # Give job time to process

                async with self.session.get(
                    f"{results_url}?output_mode=json"
                ) as response:
                    if response.status != 200:
                        return

                    data = await response.json()
                    for result in data.get("results", []):
                        event = await self._parse_splunk_result(result)
                        if event:
                            yield event

        except Exception as e:
            logger.error("Error collecting from Splunk: %s", e)

    async def _parse_splunk_result(
        self,
        result: Dict[str, Any],
    ) -> Optional[CollectedEvent]:
        """Parse Splunk result into CollectedEvent."""
        try:
            raw_text = result.get("_raw", "")

            # Identify matching security pattern
            matched_pattern = None
            for pattern in self.security_patterns:
                if any(p.lower() in raw_text.lower() for p in pattern.patterns):
                    matched_pattern = pattern
                    break

            if not matched_pattern:
                return None

            return CollectedEvent(
                collector_type="LogAggregation",
                source=f"splunk:{result.get('index', 'unknown')}",
                severity=matched_pattern.severity,
                raw_data=result,
                parsed_data={
                    "pattern_name": matched_pattern.name,
                    "host": result.get("host"),
                    "source": result.get("source"),
                    "sourcetype": result.get("sourcetype"),
                    "mitre_techniques": matched_pattern.mitre_techniques,
                },
                tags=[
                    f"pattern:{matched_pattern.name}",
                    "backend:splunk",
                    *[f"mitre:{t}" for t in matched_pattern.mitre_techniques],
                ],
            )

        except Exception as e:
            logger.error("Error parsing Splunk result: %s", e)
            return None
