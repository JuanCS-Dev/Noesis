"""
NOESIS Memory Fortress - Vault Backup
======================================

JSON Vault Backup with Checksums for disaster recovery.

Based on:
- Triple Modular Redundancy (Fault-Tolerant Systems)
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class VaultChecksum:
    """Checksum for vault backup verification."""
    file_path: str
    checksum: str
    entry_count: int
    created_at: str


class VaultBackup:
    """
    JSON Vault Backup with Checksums.

    L4 tier storage for disaster recovery.

    Features:
    - SHA-256 checksums for each backup
    - Rotation to prevent unbounded growth
    - Integrity verification on load

    Usage:
        vault = VaultBackup(path="data/vault")
        await vault.backup(memories)
        memories = await vault.restore()
    """

    def __init__(
        self,
        vault_dir: str,
        max_backups: int = 10,
    ) -> None:
        """
        Initialize vault.

        Args:
            vault_dir: Directory for backup files
            max_backups: Maximum number of backups to keep
        """
        self._dir = Path(vault_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._max_backups = max_backups
        self._lock = asyncio.Lock()

    def _calculate_checksum(self, data: List[Dict[str, Any]]) -> str:
        """Calculate SHA-256 checksum for backup data."""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()

    async def backup(
        self,
        entries: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> VaultChecksum:
        """
        Create a vault backup.

        Args:
            entries: Memory entries to backup
            metadata: Optional metadata

        Returns:
            Checksum information
        """
        async with self._lock:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self._dir / f"backup_{timestamp}.json"

            checksum = self._calculate_checksum(entries)

            backup_data = {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "entry_count": len(entries),
                "checksum": checksum,
                "metadata": metadata or {},
                "entries": entries,
            }

            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(backup_data, f, indent=2)

            checksum_file = self._dir / "latest_checksum.json"
            with open(checksum_file, "w", encoding="utf-8") as f:
                json.dump({
                    "file": backup_file.name,
                    "checksum": checksum,
                    "entry_count": len(entries),
                    "created_at": backup_data["created_at"],
                }, f)

            await self._rotate_backups()

            logger.info(f"Vault backup: {backup_file.name} ({len(entries)} entries)")

            return VaultChecksum(
                file_path=str(backup_file),
                checksum=checksum,
                entry_count=len(entries),
                created_at=backup_data["created_at"],
            )

    async def _rotate_backups(self) -> None:
        """Remove old backups beyond max_backups."""
        backups = sorted(
            self._dir.glob("backup_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        for old_backup in backups[self._max_backups:]:
            old_backup.unlink()
            logger.info(f"Rotated vault backup: {old_backup.name}")

    async def restore(self, verify_checksum: bool = True) -> List[Dict[str, Any]]:
        """
        Restore from latest vault backup.

        Args:
            verify_checksum: Whether to verify data integrity

        Returns:
            List of restored entries

        Raises:
            ValueError: If checksum verification fails
        """
        backups = sorted(
            self._dir.glob("backup_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        if not backups:
            logger.warning("No vault backups found")
            return []

        latest = backups[0]

        with open(latest, "r", encoding="utf-8") as f:
            data = json.load(f)

        entries = data.get("entries", [])
        stored_checksum = data.get("checksum", "")

        if verify_checksum:
            calculated = self._calculate_checksum(entries)
            if calculated != stored_checksum:
                raise ValueError(
                    f"Vault checksum mismatch! Expected {stored_checksum}, got {calculated}"
                )

        logger.info(f"Restored from vault: {latest.name} ({len(entries)} entries)")

        return entries

    def get_status(self) -> Dict[str, Any]:
        """Get vault status."""
        backups = list(self._dir.glob("backup_*.json"))
        total_size = sum(f.stat().st_size for f in backups)

        latest_info = None
        checksum_file = self._dir / "latest_checksum.json"
        if checksum_file.exists():
            try:
                with open(checksum_file, "r", encoding="utf-8") as f:
                    latest_info = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        return {
            "enabled": True,
            "directory": str(self._dir),
            "backup_count": len(backups),
            "total_size_bytes": total_size,
            "latest": latest_info,
        }

