"""
Elasticsearch Backend for Log Aggregation Collector.

Elasticsearch log collection and parsing.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional

import aiohttp

from ..base_collector import CollectedEvent
from .models import LogAggregationConfig, SecurityEventPattern

logger = logging.getLogger(__name__)


class ElasticsearchMixin:
    """Mixin providing Elasticsearch collection capabilities."""

    config: LogAggregationConfig
    session: Optional[aiohttp.ClientSession]
    security_patterns: List[SecurityEventPattern]
    metrics: Any

    async def _collect_elasticsearch(
        self,
        from_time: datetime,
        to_time: datetime,
    ) -> AsyncIterator[CollectedEvent]:
        """Collect logs from Elasticsearch."""
        if not self.session:
            return

        # Build query for security events
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": from_time.isoformat(),
                                    "lte": to_time.isoformat(),
                                }
                            }
                        }
                    ],
                    "should": [
                        {"match": {"message": pattern}}
                        for security_pattern in self.security_patterns
                        for pattern in security_pattern.patterns
                    ],
                    "minimum_should_match": 1,
                }
            },
            "size": self.config.max_results_per_query,
            "sort": [{"@timestamp": "asc"}],
        }

        # Query each index
        for index in self.config.indices:
            url = f"http://{self.config.host}:{self.config.port}/{index}/_search"

            try:
                async with self.session.post(url, json=query) as response:
                    if response.status != 200:
                        self.metrics.errors_count += 1
                        continue

                    data = await response.json()
                    hits = data.get("hits", {}).get("hits", [])

                    for hit in hits:
                        event = await self._parse_elasticsearch_hit(hit)
                        if event:
                            self.metrics.events_collected += 1
                            yield event

            except Exception as e:
                logger.error("Error querying index %s: %s", index, e)
                self.metrics.errors_count += 1

    async def _parse_elasticsearch_hit(
        self,
        hit: Dict[str, Any],
    ) -> Optional[CollectedEvent]:
        """Parse Elasticsearch hit into CollectedEvent."""
        try:
            source = hit.get("_source", {})
            message = source.get("message", "")

            # Identify matching security pattern
            matched_pattern = None
            for pattern in self.security_patterns:
                if any(p.lower() in message.lower() for p in pattern.patterns):
                    matched_pattern = pattern
                    break

            if not matched_pattern:
                return None

            # Extract relevant fields
            extracted_data = {}
            for field in matched_pattern.fields_to_extract:
                if field in source:
                    extracted_data[field] = source[field]

            return CollectedEvent(
                collector_type="LogAggregation",
                source=f"elasticsearch:{hit.get('_index')}",
                severity=matched_pattern.severity,
                raw_data=source,
                parsed_data={
                    "pattern_name": matched_pattern.name,
                    "extracted_fields": extracted_data,
                    "mitre_techniques": matched_pattern.mitre_techniques,
                    "index": hit.get("_index"),
                    "doc_id": hit.get("_id"),
                },
                tags=[
                    f"pattern:{matched_pattern.name}",
                    "backend:elasticsearch",
                    *[f"mitre:{t}" for t in matched_pattern.mitre_techniques],
                ],
            )

        except Exception as e:
            logger.error("Error parsing Elasticsearch hit: %s", e)
            return None
