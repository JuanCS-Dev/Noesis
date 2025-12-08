"""
NOESIS Memory Fortress - Write-Ahead Log
=========================================

Ensures durability by logging operations before execution.

Based on:
- Write-Ahead Logging (Database Systems)
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class WALEntry:
    """Write-Ahead Log entry."""
    sequence_id: int
    operation: str
    data: Dict[str, Any]
    timestamp: str
    checksum: str
    applied: bool = False


class WriteAheadLog:
    """
    Write-Ahead Log for Memory Operations.

    Ensures durability by logging operations before execution.
    Enables crash recovery by replaying uncommitted entries.

    Format: JSONL (JSON Lines) for efficient append

    Usage:
        wal = WriteAheadLog(path="data/wal")
        seq = await wal.append("store", {"key": "value"})
        await memory.store(...)
        await wal.mark_applied(seq)
    """

    def __init__(
        self,
        wal_dir: str,
        max_entries_per_file: int = 10000,
    ) -> None:
        """
        Initialize WAL.

        Args:
            wal_dir: Directory for WAL files
            max_entries_per_file: Max entries before rotation
        """
        self._dir = Path(wal_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._max_entries = max_entries_per_file
        self._current_file: Path | None = None
        self._sequence_id = 0
        self._lock = asyncio.Lock()
        self._load_sequence()

    def _load_sequence(self) -> None:
        """Load current sequence number from existing WAL files."""
        wal_files = sorted(self._dir.glob("wal_*.jsonl"))
        if not wal_files:
            self._sequence_id = 0
            return

        latest_file = wal_files[-1]
        self._current_file = latest_file
        last_seq = 0

        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        last_seq = max(last_seq, entry.get("sequence_id", 0))
        except (json.JSONDecodeError, IOError):
            pass

        self._sequence_id = last_seq

    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate SHA-256 checksum for data integrity."""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]

    def _get_current_file(self) -> Path:
        """Get or create current WAL file."""
        if self._current_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self._current_file = self._dir / f"wal_{timestamp}.jsonl"
        return self._current_file

    async def append(self, operation: str, data: Dict[str, Any]) -> int:
        """
        Append entry to WAL.

        Args:
            operation: Operation type
            data: Operation data

        Returns:
            Sequence ID of the entry
        """
        async with self._lock:
            self._sequence_id += 1

            entry = WALEntry(
                sequence_id=self._sequence_id,
                operation=operation,
                data=data,
                timestamp=datetime.now().isoformat(),
                checksum=self._calculate_checksum(data),
                applied=False,
            )

            wal_file = self._get_current_file()
            with open(wal_file, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "sequence_id": entry.sequence_id,
                    "operation": entry.operation,
                    "data": entry.data,
                    "timestamp": entry.timestamp,
                    "checksum": entry.checksum,
                    "applied": entry.applied,
                }) + "\n")
                f.flush()

            if self._sequence_id % self._max_entries == 0:
                self._current_file = None

            return entry.sequence_id

    async def mark_applied(self, sequence_id: int) -> None:
        """Mark an entry as applied."""
        checkpoint_file = self._dir / "checkpoint.json"

        async with self._lock:
            checkpoint: Dict[str, Any] = {}
            if checkpoint_file.exists():
                try:
                    with open(checkpoint_file, "r", encoding="utf-8") as f:
                        checkpoint = json.load(f)
                except (json.JSONDecodeError, IOError):
                    pass

            checkpoint["last_applied"] = max(
                checkpoint.get("last_applied", 0),
                sequence_id
            )
            checkpoint["updated_at"] = datetime.now().isoformat()

            with open(checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(checkpoint, f)

    async def get_unapplied_entries(self) -> List[WALEntry]:
        """Get all unapplied entries for replay."""
        checkpoint_file = self._dir / "checkpoint.json"
        last_applied = 0

        if checkpoint_file.exists():
            try:
                with open(checkpoint_file, "r", encoding="utf-8") as f:
                    checkpoint = json.load(f)
                    last_applied = checkpoint.get("last_applied", 0)
            except (json.JSONDecodeError, IOError):
                pass

        entries = []
        for wal_file in sorted(self._dir.glob("wal_*.jsonl")):
            try:
                with open(wal_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            if data["sequence_id"] > last_applied:
                                entry = WALEntry(
                                    sequence_id=data["sequence_id"],
                                    operation=data["operation"],
                                    data=data["data"],
                                    timestamp=data["timestamp"],
                                    checksum=data["checksum"],
                                    applied=data.get("applied", False),
                                )
                                if entry.checksum == self._calculate_checksum(entry.data):
                                    entries.append(entry)
                                else:
                                    logger.warning(f"WAL {entry.sequence_id} checksum mismatch")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error reading WAL file {wal_file}: {e}")

        return entries

    async def cleanup_old_files(self, keep_days: int = 7) -> int:
        """Cleanup old WAL files."""
        import time
        cutoff = time.time() - (keep_days * 86400)
        deleted = 0

        for wal_file in self._dir.glob("wal_*.jsonl"):
            if wal_file.stat().st_mtime < cutoff:
                wal_file.unlink()
                deleted += 1
                logger.info(f"Deleted old WAL file: {wal_file}")

        return deleted

    def get_status(self) -> Dict[str, Any]:
        """Get WAL status."""
        files = list(self._dir.glob("wal_*.jsonl"))
        total_size = sum(f.stat().st_size for f in files)

        return {
            "enabled": True,
            "directory": str(self._dir),
            "current_sequence": self._sequence_id,
            "file_count": len(files),
            "total_size_bytes": total_size,
        }

