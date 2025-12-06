"""
Models for Log Aggregation Collector.

Configuration and pattern models.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from ..base_collector import CollectorConfig


class LogAggregationConfig(CollectorConfig):
    """Configuration for Log Aggregation Collector."""

    backend_type: str = Field(
        default="elasticsearch",
        description="Type of log backend (elasticsearch, splunk, graylog)",
    )
    host: str = Field(default="localhost", description="Log backend host")
    port: int = Field(default=9200, description="Log backend port")
    username: Optional[str] = Field(
        default=None, description="Authentication username"
    )
    password: Optional[str] = Field(
        default=None, description="Authentication password"
    )
    api_key: Optional[str] = Field(
        default=None, description="API key for authentication"
    )
    indices: List[str] = Field(
        default_factory=lambda: ["logs-*", "security-*"],
        description="Indices/indexes to query",
    )
    query_window_minutes: int = Field(
        default=5,
        description="Time window for each query in minutes",
    )
    max_results_per_query: int = Field(
        default=1000,
        description="Maximum results per query",
    )
    ssl_verify: bool = Field(default=True, description="Verify SSL certificates")

    @field_validator("backend_type")
    @classmethod
    def validate_backend_type(cls, v: str) -> str:
        """Validate backend type."""
        allowed = ["elasticsearch", "splunk", "graylog"]
        if v not in allowed:
            raise ValueError(f"backend_type must be one of {allowed}")
        return v


class SecurityEventPattern(BaseModel):
    """Pattern for identifying security events in logs."""

    name: str
    severity: str
    patterns: List[str]
    fields_to_extract: List[str]
    mitre_techniques: List[str] = Field(default_factory=list)
