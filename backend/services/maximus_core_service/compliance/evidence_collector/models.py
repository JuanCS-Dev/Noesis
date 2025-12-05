"""Evidence Collector Models.

Data structures for evidence items and packages.
"""

from __future__ import annotations

import hashlib
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..base import Evidence, RegulationType

logger = logging.getLogger(__name__)


@dataclass
class EvidenceItem:
    """Single evidence item with metadata and integrity information.

    Attributes:
        evidence: Core evidence object.
        file_size: Size of evidence file in bytes.
        collected_from: Source path/system.
        integrity_verified: Whether integrity has been verified.
        verification_timestamp: When integrity was last verified.
    """

    evidence: Evidence
    file_size: int = 0
    collected_from: str = ""
    integrity_verified: bool = False
    verification_timestamp: datetime | None = None

    def verify_integrity(self, file_path: str) -> bool:
        """Verify evidence file integrity using SHA-256 hash.

        Args:
            file_path: Path to evidence file.

        Returns:
            True if integrity verified.
        """
        if not os.path.exists(file_path):
            logger.error(f"Evidence file not found: {file_path}")
            return False

        current_hash = calculate_file_hash(file_path)

        if self.evidence.file_hash == current_hash:
            self.integrity_verified = True
            self.verification_timestamp = datetime.utcnow()
            return True

        logger.warning(
            f"Evidence integrity check failed for {self.evidence.evidence_id}: "
            f"expected {self.evidence.file_hash}, got {current_hash}"
        )
        return False


@dataclass
class EvidencePackage:
    """Package of evidence for audit/compliance check.

    Attributes:
        package_id: Unique package identifier.
        regulation_type: Type of regulation.
        created_at: Package creation timestamp.
        created_by: Who created the package.
        control_ids: List of control IDs included.
        evidence_items: List of evidence items.
        package_path: Path where package is exported.
        total_size_bytes: Total size of all evidence.
        manifest: Package manifest dictionary.
    """

    package_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    regulation_type: RegulationType = RegulationType.ISO_27001
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "evidence_collector"
    control_ids: list[str] = field(default_factory=list)
    evidence_items: list[EvidenceItem] = field(default_factory=list)
    package_path: str | None = None
    total_size_bytes: int = 0
    manifest: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Calculate package metadata."""
        self.total_size_bytes = sum(item.file_size for item in self.evidence_items)
        self.manifest = self._build_manifest()

    def _build_manifest(self) -> dict[str, Any]:
        """Build package manifest."""
        return {
            "package_id": self.package_id,
            "regulation": self.regulation_type.value,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "total_evidence_items": len(self.evidence_items),
            "total_size_bytes": self.total_size_bytes,
            "controls": self.control_ids,
            "evidence": [
                {
                    "evidence_id": item.evidence.evidence_id,
                    "type": item.evidence.evidence_type.value,
                    "control_id": item.evidence.control_id,
                    "title": item.evidence.title,
                    "collected_at": item.evidence.collected_at.isoformat(),
                    "file_path": item.evidence.file_path,
                    "file_hash": item.evidence.file_hash,
                    "file_size": item.file_size,
                }
                for item in self.evidence_items
            ],
        }

    def get_evidence_for_control(self, control_id: str) -> list[EvidenceItem]:
        """Get all evidence for specific control.

        Args:
            control_id: Control ID to filter by.

        Returns:
            List of evidence items for the control.
        """
        return [
            item
            for item in self.evidence_items
            if item.evidence.control_id == control_id
        ]


def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA-256 hash of file.

    Args:
        file_path: Path to file.

    Returns:
        Hex-encoded SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
