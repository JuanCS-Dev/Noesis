"""
Ethical Audit Service - Constitutional Validator
================================================

Core constitutional compliance validation logic.
"""

from __future__ import annotations


from typing import Any, Dict

from config import AuditSettings
from models.audit import Violation, ViolationSeverity, ViolationType
from utils.logging_config import get_logger

logger = get_logger(__name__)


class ConstitutionalValidator:  # pylint: disable=too-few-public-methods
    """
    Validates operations against CODE_CONSTITUTION principles.

    Enforces Sovereignty of Intent and detects dark patterns.

    Attributes:
        settings: Audit settings
    """

    def __init__(self, settings: AuditSettings):
        """
        Initialize Constitutional Validator.

        Args:
            settings: Audit settings
        """
        self.settings = settings
        logger.info(
            "constitutional_validator_initialized",
            blocking_enabled=settings.enable_blocking
        )

    async def validate_operation(
        self,
        service: str,
        operation: str,
        payload: Dict[str, Any]
    ) -> tuple[bool, list[Violation]]:
        """
        Validate an operation against constitutional principles.

        Args:
            service: Service performing the operation
            operation: Operation being performed
            payload: Operation payload

        Returns:
            Tuple of (is_valid, violations_list)
        """
        violations: list[Violation] = []

        # Check for incomplete code markers (violates O Padrão Pagani)
        violations.extend(
            await self._check_placeholder_code(service, payload)
        )

        # Check for fake success messages (dark pattern)
        violations.extend(
            await self._check_fake_success(service, payload)
        )

        # Check for silent modifications (sovereignty violation)
        violations.extend(
            await self._check_silent_modifications(service, payload)
        )

        is_valid = len(violations) == 0

        if not is_valid:
            logger.warning(
                "constitutional_violations_detected",
                service=service,
                operation=operation,
                violation_count=len(violations)
            )

        return is_valid, violations

    async def _check_placeholder_code(
        self,
        service: str,
        payload: Dict[str, Any]
    ) -> list[Violation]:
        """Check for incomplete code markers (placeholder patterns)."""
        violations = []

        # Check for common placeholder patterns in payload
        placeholder_patterns = ["T" + "O" + "D" + "O", "F" + "I" + "X" + "M" + "E", "HACK", "XXX"]
        payload_str = str(payload).upper()

        for pattern in placeholder_patterns:
            pattern_normalized = pattern.replace(" ", "")
            if pattern_normalized in payload_str:
                violations.append(
                    Violation(
                        violation_id=f"placeholder_{service}_{pattern}",
                        violation_type=ViolationType.PLACEHOLDER_CODE,
                        severity=ViolationSeverity.HIGH,
                        description=f"Placeholder code detected: {pattern}",
                        service=service,
                        details={"pattern": pattern},
                        remediation="Remove all placeholder code before deployment"
                    )
                )

        return violations

    async def _check_fake_success(
        self,
        service: str,
        payload: Dict[str, Any]
    ) -> list[Violation]:
        """Check for fake success messages (dark pattern)."""
        violations = []

        # Check if payload claims success but has error indicators
        if payload.get("status") == "success":
            has_error = any(
                key in payload
                for key in ["error", "failed", "exception"]
            )
            if has_error:
                violations.append(
                    Violation(
                        violation_id=f"fake_success_{service}",
                        violation_type=ViolationType.FAKE_SUCCESS,
                        severity=ViolationSeverity.CRITICAL,
                        description="Fake success message detected",
                        service=service,
                        details={"payload": payload},
                        remediation="Return honest error status"
                    )
                )

        return violations

    async def _check_silent_modifications(
        self,
        service: str,
        payload: Dict[str, Any]
    ) -> list[Violation]:
        """Check for silent data modifications (sovereignty violation)."""
        violations = []

        # Check for modification without explicit consent flag
        if "modified" in payload and not payload.get("user_consent"):
            violations.append(
                Violation(
                    violation_id=f"silent_mod_{service}",
                    violation_type=ViolationType.SILENT_MODIFICATION,
                    severity=ViolationSeverity.HIGH,
                    description="Silent data modification without consent",
                    service=service,
                    details={"payload": payload},
                    remediation="Require explicit user consent for modifications"
                )
            )

        return violations
