"""Evidence Collector.

Automated evidence collection system for compliance verification.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from ..base import (
    ComplianceConfig,
    Control,
    Evidence,
    EvidenceType,
    RegulationType,
)
from .models import EvidenceItem, EvidencePackage, calculate_file_hash

logger = logging.getLogger(__name__)


class EvidenceCollector:
    """Automated evidence collection system.

    Collects evidence from multiple sources and organizes by control.

    Attributes:
        config: Compliance configuration.
    """

    def __init__(self, config: ComplianceConfig | None = None) -> None:
        """Initialize evidence collector.

        Args:
            config: Compliance configuration.
        """
        self.config = config or ComplianceConfig()
        self._evidence_cache: dict[str, list[EvidenceItem]] = {}

        os.makedirs(self.config.evidence_storage_path, exist_ok=True)
        logger.info(
            f"Evidence collector initialized, storage: "
            f"{self.config.evidence_storage_path}"
        )

    def collect_log_evidence(
        self,
        control: Control,
        log_path: str,
        title: str,
        description: str,
        expiration_days: int = 90,
    ) -> EvidenceItem | None:
        """Collect log file as evidence.

        Args:
            control: Control this evidence supports.
            log_path: Path to log file.
            title: Evidence title.
            description: Evidence description.
            expiration_days: Days until evidence expires.

        Returns:
            Evidence item or None if collection failed.
        """
        return self._collect_evidence(
            control=control,
            source_path=log_path,
            title=title,
            description=description,
            evidence_type=EvidenceType.LOG,
            file_suffix="_log.txt",
            expiration_days=expiration_days,
        )

    def collect_configuration_evidence(
        self,
        control: Control,
        config_path: str,
        title: str,
        description: str,
        expiration_days: int = 180,
    ) -> EvidenceItem | None:
        """Collect configuration file as evidence.

        Args:
            control: Control this evidence supports.
            config_path: Path to configuration file.
            title: Evidence title.
            description: Evidence description.
            expiration_days: Days until evidence expires.

        Returns:
            Evidence item or None if collection failed.
        """
        return self._collect_evidence(
            control=control,
            source_path=config_path,
            title=title,
            description=description,
            evidence_type=EvidenceType.CONFIGURATION,
            file_suffix="_config.txt",
            expiration_days=expiration_days,
        )

    def collect_test_evidence(
        self,
        control: Control,
        test_result_path: str,
        title: str,
        description: str,
        expiration_days: int = 90,
    ) -> EvidenceItem | None:
        """Collect test results as evidence.

        Args:
            control: Control this evidence supports.
            test_result_path: Path to test results file.
            title: Evidence title.
            description: Evidence description.
            expiration_days: Days until evidence expires.

        Returns:
            Evidence item or None if collection failed.
        """
        return self._collect_evidence(
            control=control,
            source_path=test_result_path,
            title=title,
            description=description,
            evidence_type=EvidenceType.TEST_RESULT,
            file_suffix="_test.txt",
            expiration_days=expiration_days,
        )

    def collect_document_evidence(
        self,
        control: Control,
        doc_path: str,
        title: str,
        description: str,
        expiration_days: int = 365,
    ) -> EvidenceItem | None:
        """Collect document as evidence.

        Args:
            control: Control this evidence supports.
            doc_path: Path to document.
            title: Evidence title.
            description: Evidence description.
            expiration_days: Days until evidence expires.

        Returns:
            Evidence item or None if collection failed.
        """
        file_ext = Path(doc_path).suffix
        return self._collect_evidence(
            control=control,
            source_path=doc_path,
            title=title,
            description=description,
            evidence_type=EvidenceType.DOCUMENT,
            file_suffix=f"_doc{file_ext}",
            expiration_days=expiration_days,
        )

    def collect_policy_evidence(
        self,
        control: Control,
        policy_path: str,
        title: str,
        description: str,
    ) -> EvidenceItem | None:
        """Collect organizational policy as evidence.

        Args:
            control: Control this evidence supports.
            policy_path: Path to policy document.
            title: Evidence title.
            description: Evidence description.

        Returns:
            Evidence item or None if collection failed.
        """
        file_ext = Path(policy_path).suffix
        return self._collect_evidence(
            control=control,
            source_path=policy_path,
            title=title,
            description=description,
            evidence_type=EvidenceType.POLICY,
            file_suffix=f"_policy{file_ext}",
            expiration_days=365,
        )

    def _collect_evidence(
        self,
        control: Control,
        source_path: str,
        title: str,
        description: str,
        evidence_type: EvidenceType,
        file_suffix: str,
        expiration_days: int,
    ) -> EvidenceItem | None:
        """Internal method to collect evidence of any type.

        Args:
            control: Control this evidence supports.
            source_path: Path to source file.
            title: Evidence title.
            description: Evidence description.
            evidence_type: Type of evidence.
            file_suffix: Suffix for evidence filename.
            expiration_days: Days until evidence expires.

        Returns:
            Evidence item or None if collection failed.
        """
        if not os.path.exists(source_path):
            logger.warning(f"Source file not found: {source_path}")
            return None

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        evidence_filename = f"{control.control_id}_{timestamp}{file_suffix}"
        evidence_path = os.path.join(
            self.config.evidence_storage_path, evidence_filename
        )

        try:
            shutil.copy2(source_path, evidence_path)
        except Exception as e:
            logger.error(f"Failed to copy file: {e}")
            return None

        file_hash = calculate_file_hash(evidence_path)
        file_size = os.path.getsize(evidence_path)

        evidence = Evidence(
            evidence_type=evidence_type,
            control_id=control.control_id,
            title=title,
            description=description,
            collected_by="evidence_collector",
            file_path=evidence_path,
            file_hash=file_hash,
            expiration_date=datetime.utcnow() + timedelta(days=expiration_days),
        )

        evidence_item = EvidenceItem(
            evidence=evidence,
            file_size=file_size,
            collected_from=source_path,
            integrity_verified=True,
            verification_timestamp=datetime.utcnow(),
        )

        if control.control_id not in self._evidence_cache:
            self._evidence_cache[control.control_id] = []
        self._evidence_cache[control.control_id].append(evidence_item)

        logger.info(
            f"Collected {evidence_type.value} evidence for "
            f"{control.control_id}: {title}"
        )
        return evidence_item

    def get_evidence_for_control(self, control_id: str) -> list[Evidence]:
        """Get all collected evidence for a control.

        Args:
            control_id: Control ID.

        Returns:
            List of evidence items.
        """
        if control_id not in self._evidence_cache:
            return []
        return [item.evidence for item in self._evidence_cache[control_id]]

    def get_all_evidence(self) -> dict[str, list[Evidence]]:
        """Get all collected evidence organized by control.

        Returns:
            Dict mapping control_id -> evidence list.
        """
        return {
            control_id: [item.evidence for item in items]
            for control_id, items in self._evidence_cache.items()
        }

    def create_evidence_package(
        self,
        regulation_type: RegulationType,
        control_ids: list[str] | None = None,
    ) -> EvidencePackage:
        """Create evidence package for audit.

        Args:
            regulation_type: Regulation type.
            control_ids: Optional list of control IDs (all if None).

        Returns:
            Evidence package.
        """
        logger.info(f"Creating evidence package for {regulation_type.value}")

        if control_ids:
            evidence_items = [
                item
                for control_id, items in self._evidence_cache.items()
                if control_id in control_ids
                for item in items
            ]
            included_controls = control_ids
        else:
            evidence_items = [
                item for items in self._evidence_cache.values() for item in items
            ]
            included_controls = list(self._evidence_cache.keys())

        package = EvidencePackage(
            regulation_type=regulation_type,
            control_ids=included_controls,
            evidence_items=evidence_items,
        )

        logger.info(
            f"Evidence package created: {package.package_id}, "
            f"{len(evidence_items)} items, {package.total_size_bytes} bytes"
        )
        return package

    def export_evidence_package(
        self,
        package: EvidencePackage,
        export_path: str,
    ) -> bool:
        """Export evidence package to directory for auditor.

        Args:
            package: Evidence package to export.
            export_path: Directory to export to.

        Returns:
            True if export successful.
        """
        logger.info(
            f"Exporting evidence package {package.package_id} to {export_path}"
        )

        try:
            os.makedirs(export_path, exist_ok=True)

            for item in package.evidence_items:
                if item.evidence.file_path and os.path.exists(item.evidence.file_path):
                    filename = os.path.basename(item.evidence.file_path)
                    dest_path = os.path.join(export_path, filename)
                    shutil.copy2(item.evidence.file_path, dest_path)

            manifest_path = os.path.join(export_path, "manifest.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(package.manifest, f, indent=2)

            package.package_path = export_path
            logger.info(f"Evidence package exported successfully to {export_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export evidence package: {e}")
            return False

    def verify_all_evidence(self) -> dict[str, bool]:
        """Verify integrity of all collected evidence.

        Returns:
            Dict mapping evidence_id -> verification result.
        """
        logger.info("Verifying integrity of all collected evidence")

        results: dict[str, bool] = {}

        for items in self._evidence_cache.values():
            for item in items:
                if item.evidence.file_path:
                    verified = item.verify_integrity(item.evidence.file_path)
                    results[item.evidence.evidence_id] = verified

        passed = sum(1 for v in results.values() if v)
        logger.info(
            f"Evidence integrity verification complete: {passed}/{len(results)} passed"
        )
        return results

    def get_expired_evidence(self) -> list[Evidence]:
        """Get all evidence that has expired.

        Returns:
            List of expired evidence.
        """
        expired = []
        for items in self._evidence_cache.values():
            for item in items:
                if item.evidence.is_expired():
                    expired.append(item.evidence)
        return expired
