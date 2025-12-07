"""Models for data collection module."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class DataSourceType(Enum):
    """Supported data source types."""

    ELASTIC = "elasticsearch"
    SPLUNK = "splunk"
    QRADAR = "qradar"
    JSON_FILE = "json_file"
    CSV_FILE = "csv_file"
    PARQUET_FILE = "parquet_file"
    ZEEK_LOGS = "zeek_logs"
    SURICATA_LOGS = "suricata_logs"


@dataclass
class DataSource:
    """Configuration for a data source."""

    name: str
    source_type: DataSourceType
    connection_params: dict[str, Any]
    query_filter: str | None = None
    time_field: str = "@timestamp"
    batch_size: int = 1000

    def __repr__(self) -> str:
        return f"DataSource(name={self.name}, type={self.source_type.value})"


@dataclass
class CollectedEvent:
    """Represents a collected security event."""

    event_id: str
    timestamp: datetime
    source: str
    event_type: str
    raw_data: dict[str, Any]
    labels: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "event_type": self.event_type,
            "raw_data": self.raw_data,
            "labels": self.labels or {},
        }
