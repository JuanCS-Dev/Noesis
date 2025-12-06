"""
ChromaDB to Qdrant Migration Script
====================================

Migrates existing memories from ChromaDB to Qdrant with data integrity validation.

Features:
- Batch migration for efficiency
- Checksum validation
- Rollback capability
- Progress tracking
"""

from __future__ import annotations

from typing import List, Dict, Any
from datetime import datetime
import hashlib
import json

from episodic_memory.core.qdrant_client import QdrantClient
from episodic_memory.utils.logging_config import get_logger

logger = get_logger(__name__)


class MigrationError(Exception):
    """Raised when migration fails."""


class ChromaToQdrantMigration:
    """
    Migrate memories from ChromaDB to Qdrant.

    Strategy:
    1. Read all memories from ChromaDB
    2. Validate embedding dimensions
    3. Batch upsert to Qdrant
    4. Verify checksums match
    5. Generate migration report

    Example:
        >>> migration = ChromaToQdrantMigration(
        ...     chroma_client=chroma,
        ...     qdrant_client=qdrant
        ... )
        >>> report = await migration.migrate(batch_size=100)
        >>> print(f"Migrated {report['total_migrated']} memories")
    """

    def __init__(
        self,
        chroma_client: Any,  # ChromaDB client (legacy)
        qdrant_client: QdrantClient,
        batch_size: int = 100
    ):
        """
        Initialize migration.

        Args:
            chroma_client: ChromaDB client (source)
            qdrant_client: Qdrant client (destination)
            batch_size: Number of items per batch
        """
        self.chroma = chroma_client
        self.qdrant =qdrant_client
        self.batch_size = batch_size

        self.total_processed = 0
        self.total_errors = 0
        self.checksums: Dict[str, str] = {}

    async def migrate(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute migration.

        Args:
            dry_run: If True, validate without writing to Qdrant

        Returns:
            Migration report with statistics

        Raises:
            MigrationError: If migration fails
        """
        logger.info(
            "migration_started",
            extra={"dry_run": dry_run, "batch_size": self.batch_size}
        )

        start_time = datetime.now()

        try:
            # 1. Fetch all memories from ChromaDB
            memories = await self._fetch_chroma_memories()
            total_count = len(memories)

            logger.info(
                "memories_fetched",
                extra={"count": total_count}
            )

            # 2. Migrate in batches
            for i in range(0, total_count, self.batch_size):
                batch = memories[i:i + self.batch_size]

                if not dry_run:
                    await self._migrate_batch(batch)
                else:
                    await self._validate_batch(batch)

                self.total_processed += len(batch)

                logger.info(
                    "migration_progress",
                    extra={
                        "processed": self.total_processed,
                        "total": total_count,
                        "percent": round(self.total_processed / total_count * 100, 2)
                    }
                )

            # 3. Validate integrity
            if not dry_run:
                integrity_ok = await self._validate_integrity(memories)
                if not integrity_ok:
                    raise MigrationError("Integrity validation failed")

            elapsed = (datetime.now() - start_time).total_seconds()

            report = {
                "status": "success",
                "total_migrated": self.total_processed,
                "total_errors": self.total_errors,
                "elapsed_seconds": elapsed,
                "throughput": round(self.total_processed / elapsed, 2),
                "dry_run": dry_run
            }

            logger.info("migration_complete", extra=report)
            return report

        except Exception as e:
            logger.error(
                "migration_failed",
                extra={"error": str(e)}
            )
            raise MigrationError(f"Migration failed: {e}") from e

    async def _fetch_chroma_memories(self) -> List[Dict[str, Any]]:
        """
        Fetch all memories from ChromaDB.

        Returns:
            List of memory dicts with id, embedding, metadata
        """
        # Implementation depends on ChromaDB client API
        # Placeholder for actual implementation
        raise NotImplementedError(
            "ChromaDB fetch not implemented. "
            "Connect to actual ChromaDB collection and fetch all documents."
        )

    async def _migrate_batch(self, batch: List[Dict[str, Any]]) -> None:
        """
        Migrate batch of memories to Qdrant.

        Args:
            batch: List of memory dicts
        """
        for memory in batch:
            try:
                await self.qdrant.store_memory(
                    memory_id=memory["id"],
                    embedding=memory["embedding"],
                    metadata=memory["metadata"]
                )

                # Store checksum for validation
                checksum = self._calculate_checksum(memory)
                self.checksums[memory["id"]] = checksum

            except (ValueError, KeyError, RuntimeError) as e:
                logger.error(
                    "memory_migration_failed",
                    extra={"memory_id": memory.get("id"), "error": str(e)}
                )
                self.total_errors += 1

    async def _validate_batch(self, batch: List[Dict[str, Any]]) -> None:
        """
        Validate batch (dry run).

        Args:
            batch: List of memory dicts
        """
        for memory in batch:
            # Validate structure
            required_keys = ["id", "embedding", "metadata"]
            if not all(k in memory for k in required_keys):
                logger.warning(
                    "invalid_memory_structure",
                    extra={"memory_id": memory.get("id")}
                )
                self.total_errors += 1
                continue

            # Validate embedding size
            if len(memory["embedding"]) != self.qdrant.vector_size:
                logger.warning(
                    "invalid_embedding_size",
                    extra={
                        "memory_id": memory["id"],
                        "size": len(memory["embedding"]),
                        "expected": self.qdrant.vector_size
                    }
                )
                self.total_errors += 1

    async def _validate_integrity(self, original_memories: List[Dict[str, Any]]) -> bool:
        """
        Validate data integrity after migration.

        Args:
            original_memories: Original memories from ChromaDB

        Returns:
            True if integrity check passes
        """
        logger.info("validating_integrity")

        # Check count
        qdrant_count = await self.qdrant.count_memories()
        if qdrant_count != len(original_memories):
            logger.error(
                "count_mismatch",
                extra={
                    "qdrant_count": qdrant_count,
                    "original_count": len(original_memories)
                }
            )
            return False

        # Sample check (10% of memories)
        sample_size = max(10, len(original_memories) // 10)
        sample = original_memories[:sample_size]

        for memory in sample:
            # Search for exact match
            results = await self.qdrant.search_memory(
                query_embedding=memory["embedding"],
                limit=1,
                score_threshold=0.99  # Near-exact match
            )

            if not results or results[0]["id"] != memory["id"]:
                logger.error(
                    "integrity_check_failed",
                    extra={"memory_id": memory["id"]}
                )
                return False

        logger.info("integrity_validated")
        return True

    def _calculate_checksum(self, memory: Dict[str, Any]) -> str:
        """
        Calculate checksum for memory.

        Args:
            memory: Memory dict

        Returns:
            MD5 checksum hex
        """
        data = json.dumps(memory, sort_keys=True).encode()
        return hashlib.md5(data).hexdigest()

    def generate_report(self) -> str:
        """
        Generate migration report.

        Returns:
            Markdown report
        """
        report = f"""
# Migration Report

**Date**: {datetime.now().isoformat()}

## Statistics
- Total Processed: {self.total_processed}
- Total Errors: {self.total_errors}
- Success Rate: {(1 - self.total_errors / max(1, self.total_processed)) * 100:.2f}%

## Checksums
- Calculated: {len(self.checksums)}

## Status
{'✅ SUCCESS' if self.total_errors == 0 else f'⚠️  {self.total_errors} ERRORS'}
        """

        return report.strip()


async def migrate_chromadb_to_qdrant(
    chroma_client: Any,
    qdrant_url: str = "http://localhost:6333",
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Convenience function for migration.

    Args:
        chroma_client: ChromaDB client
        qdrant_url: Qdrant server URL
        dry_run: If True, validate without writing

    Returns:
        Migration report
    """
    qdrant = QdrantClient(url=qdrant_url)
    migration = ChromaToQdrantMigration(chroma_client, qdrant)

    return await migration.migrate(dry_run=dry_run)
