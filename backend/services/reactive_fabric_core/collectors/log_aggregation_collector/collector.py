"""
Main Log Aggregation Collector Class.

Collector for aggregating and analyzing logs from centralized systems.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, AsyncIterator, List, Optional

import aiohttp

from ..base_collector import BaseCollector, CollectedEvent
from .elasticsearch import ElasticsearchMixin
from .graylog import GraylogMixin
from .models import LogAggregationConfig, SecurityEventPattern
from .patterns import init_security_patterns
from .splunk import SplunkMixin

logger = logging.getLogger(__name__)


class LogAggregationCollector(
    BaseCollector,
    ElasticsearchMixin,
    SplunkMixin,
    GraylogMixin,
):
    """
    Collector for aggregating and analyzing logs from centralized systems.

    Supports Elasticsearch, Splunk, and Graylog backends.
    Focuses on security-relevant events and patterns.
    """

    def __init__(self, config: LogAggregationConfig) -> None:
        """Initialize the log aggregation collector."""
        super().__init__(config)
        self.config: LogAggregationConfig = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_query_time = datetime.utcnow() - timedelta(
            minutes=config.query_window_minutes
        )

        # Define security event patterns
        self.security_patterns: List[SecurityEventPattern] = init_security_patterns()

    async def initialize(self) -> None:
        """Initialize connection to log aggregation backend."""
        # Create HTTP session with appropriate auth
        auth = None
        headers: dict[str, str] = {}

        if self.config.username and self.config.password:
            auth = aiohttp.BasicAuth(self.config.username, self.config.password)
        elif self.config.api_key:
            if self.config.backend_type == "elasticsearch":
                headers["Authorization"] = f"ApiKey {self.config.api_key}"
            elif self.config.backend_type == "splunk":
                headers["Authorization"] = f"Bearer {self.config.api_key}"

        connector = aiohttp.TCPConnector(ssl=self.config.ssl_verify)
        self.session = aiohttp.ClientSession(
            auth=auth,
            headers=headers,
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds),
        )

        logger.info("Initialized %s collector", self.config.backend_type)

    async def validate_source(self) -> bool:
        """Validate connection to log backend."""
        if not self.session:
            return False

        try:
            if self.config.backend_type == "elasticsearch":
                url = (
                    f"http://{self.config.host}:{self.config.port}/_cluster/health"
                )
                async with self.session.get(url) as response:
                    return response.status == 200

            elif self.config.backend_type == "splunk":
                url = (
                    f"https://{self.config.host}:{self.config.port}"
                    "/services/server/info"
                )
                async with self.session.get(url) as response:
                    return response.status == 200

            elif self.config.backend_type == "graylog":
                url = (
                    f"http://{self.config.host}:{self.config.port}"
                    "/api/system/cluster"
                )
                async with self.session.get(url) as response:
                    return response.status == 200

            return False

        except Exception as e:
            logger.error("Source validation failed: %s", e)
            return False

    async def collect(self) -> AsyncIterator[CollectedEvent]:
        """Collect and analyze logs from the backend."""
        current_time = datetime.utcnow()

        # Query logs for the time window
        query_from = self.last_query_time
        query_to = current_time

        try:
            if self.config.backend_type == "elasticsearch":
                async for event in self._collect_elasticsearch(query_from, query_to):
                    yield event

            elif self.config.backend_type == "splunk":
                async for event in self._collect_splunk(query_from, query_to):
                    yield event

            elif self.config.backend_type == "graylog":
                async for event in self._collect_graylog(query_from, query_to):
                    yield event

            # Update last query time after successful collection
            self.last_query_time = query_to

        except Exception as e:
            logger.error("Error collecting logs: %s", e)
            self.metrics.errors_count += 1

    async def cleanup(self) -> None:
        """Clean up collector resources."""
        if self.session:
            await self.session.close()
            self.session = None
        logger.info("Cleaned up %s collector", self.config.backend_type)

    def __repr__(self) -> str:
        """String representation of the log aggregation collector."""
        return (
            f"LogAggregationCollector("
            f"backend={self.config.backend_type}, "
            f"host={self.config.host}, "
            f"health={self.metrics.health.value}, "
            f"events={self.metrics.events_collected}, "
            f"errors={self.metrics.errors_count})"
        )
