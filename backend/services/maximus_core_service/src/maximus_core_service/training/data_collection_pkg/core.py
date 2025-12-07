"""Core data collection implementation."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

import pandas as pd

from .models import CollectedEvent, DataSource, DataSourceType

logger = logging.getLogger(__name__)


class DataCollector:
    """Collects security events from multiple sources for training."""

    def __init__(
        self,
        sources: list[DataSource],
        output_dir: Path | None = None,
        checkpoint_enabled: bool = True,
    ) -> None:
        """Initialize data collector."""
        self.sources = sources
        self.output_dir = Path(output_dir) if output_dir else Path("training/data/raw")
        self.checkpoint_enabled = checkpoint_enabled

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.stats = {
            "events_collected": 0,
            "events_deduplicated": 0,
            "errors": 0,
            "sources_processed": 0,
        }

        self._seen_event_ids: set = set()

        logger.info("DataCollector initialized with %s sources", len(sources))

    def collect(
        self,
        start_date: str | datetime | None = None,
        end_date: str | datetime | None = None,
        max_events: int | None = None,
        resume_from_checkpoint: bool = True,
    ) -> Iterator[CollectedEvent]:
        """Collect events from all configured sources."""
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)

        events_collected = 0

        for source in self.sources:
            try:
                logger.info("Collecting from source: %s", source.name)

                for event in self._collect_from_source(source, start_date, end_date):
                    if event.event_id in self._seen_event_ids:
                        self.stats["events_deduplicated"] += 1
                        continue

                    self._seen_event_ids.add(event.event_id)
                    self.stats["events_collected"] += 1
                    events_collected += 1

                    yield event

                    if max_events and events_collected >= max_events:
                        logger.info("Reached max_events limit: %s", max_events)
                        return

                self.stats["sources_processed"] += 1

            except Exception as e:
                logger.error("Error collecting from %s: %s", source.name, e)
                self.stats["errors"] += 1

        logger.info("Collection complete: %s events collected", events_collected)

    def _collect_from_source(
        self,
        source: DataSource,
        start_date: datetime | None,
        end_date: datetime | None,
    ) -> Iterator[CollectedEvent]:
        """Collect from a single source."""
        if source.source_type == DataSourceType.JSON_FILE:
            yield from self._collect_from_json_file(source)
        elif source.source_type == DataSourceType.CSV_FILE:
            yield from self._collect_from_csv_file(source)
        elif source.source_type == DataSourceType.PARQUET_FILE:
            yield from self._collect_from_parquet_file(source)
        else:
            logger.warning("Unsupported source type: %s", source.source_type)

    def _collect_from_json_file(self, source: DataSource) -> Iterator[CollectedEvent]:
        """Collect from JSON file."""
        file_path = Path(source.connection_params["path"])

        if not file_path.exists():
            logger.error("File not found: %s", file_path)
            return

        with open(file_path) as f:
            data = json.load(f)

        events = data if isinstance(data, list) else [data]

        for idx, event_data in enumerate(events):
            try:
                event = CollectedEvent(
                    event_id=event_data.get("id", f"{source.name}_{idx}"),
                    timestamp=datetime.fromisoformat(
                        event_data.get(source.time_field, datetime.utcnow().isoformat())
                    ),
                    source=source.name,
                    event_type=event_data.get("event_type", "unknown"),
                    raw_data=event_data,
                    labels=event_data.get("labels"),
                )
                yield event
            except Exception as e:
                logger.error("Error parsing event %s: %s", idx, e)

    def _collect_from_csv_file(self, source: DataSource) -> Iterator[CollectedEvent]:
        """Collect from CSV file."""
        file_path = Path(source.connection_params["path"])

        if not file_path.exists():
            logger.error("File not found: %s", file_path)
            return

        df = pd.read_csv(file_path)

        for idx, row in df.iterrows():
            try:
                event = CollectedEvent(
                    event_id=str(row.get("id", f"{source.name}_{idx}")),
                    timestamp=pd.to_datetime(row.get(source.time_field, datetime.utcnow())),
                    source=source.name,
                    event_type=str(row.get("event_type", "unknown")),
                    raw_data=row.to_dict(),
                )
                yield event
            except Exception as e:
                logger.error("Error parsing row %s: %s", idx, e)

    def _collect_from_parquet_file(self, source: DataSource) -> Iterator[CollectedEvent]:
        """Collect from Parquet file."""
        file_path = Path(source.connection_params["path"])

        if not file_path.exists():
            logger.error("File not found: %s", file_path)
            return

        df = pd.read_parquet(file_path)

        for idx, row in df.iterrows():
            try:
                event = CollectedEvent(
                    event_id=str(row.get("id", f"{source.name}_{idx}")),
                    timestamp=pd.to_datetime(row.get(source.time_field, datetime.utcnow())),
                    source=source.name,
                    event_type=str(row.get("event_type", "unknown")),
                    raw_data=row.to_dict(),
                )
                yield event
            except Exception as e:
                logger.error("Error parsing row %s: %s", idx, e)

    def get_statistics(self) -> dict[str, int]:
        """Get collection statistics."""
        return self.stats.copy()

    def save_collected_events(self, events: list[CollectedEvent], filename: str = "collected_events.json") -> None:
        """Save collected events to file."""
        output_path = self.output_dir / filename

        events_data = [event.to_dict() for event in events]

        with open(output_path, "w") as f:
            json.dump(events_data, f, indent=2)

        logger.info("Saved %s events to %s", len(events), output_path)
