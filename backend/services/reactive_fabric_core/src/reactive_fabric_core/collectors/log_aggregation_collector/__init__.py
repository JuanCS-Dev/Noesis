"""
Log Aggregation Collector Package.

Centralized log analysis from Elasticsearch, Splunk, and Graylog.
"""

from __future__ import annotations

from .collector import LogAggregationCollector
from .elasticsearch import ElasticsearchMixin
from .graylog import GraylogMixin
from .models import LogAggregationConfig, SecurityEventPattern
from .patterns import init_security_patterns
from .splunk import SplunkMixin

__all__ = [
    "LogAggregationCollector",
    "LogAggregationConfig",
    "SecurityEventPattern",
    "ElasticsearchMixin",
    "SplunkMixin",
    "GraylogMixin",
    "init_security_patterns",
]
