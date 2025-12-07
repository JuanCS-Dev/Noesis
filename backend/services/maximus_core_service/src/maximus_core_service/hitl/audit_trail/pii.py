"""
PII Redaction for Audit Trail.

Provides PII redaction capabilities for privacy compliance (GDPR, HIPAA).
"""

from __future__ import annotations

from typing import Any


class PIIRedactor:
    """
    PII redaction for audit entries.

    Redacts sensitive personally identifiable information from audit logs
    for privacy compliance.
    """

    DEFAULT_PII_FIELDS = [
        "context_snapshot.user_email",
        "context_snapshot.user_name",
        "context_snapshot.ip_address",
        "decision_snapshot.metadata.pii_data",
    ]

    def __init__(self, pii_fields: list[str] | None = None):
        """
        Initialize PII redactor.

        Args:
            pii_fields: List of field paths to redact (uses dot notation)
        """
        self.pii_fields = pii_fields or self.DEFAULT_PII_FIELDS

    def redact(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Redact PII fields from data dictionary.

        Args:
            data: Data dictionary to redact

        Returns:
            Redacted copy of data
        """
        redacted = data.copy()

        for field_path in self.pii_fields:
            self._redact_field(redacted, field_path)

        return redacted

    def _redact_field(self, data: dict[str, Any], field_path: str) -> None:
        """
        Redact single field using dot notation path.

        Args:
            data: Data dictionary
            field_path: Dot-separated field path (e.g., "context.user_email")
        """
        parts = field_path.split(".")
        current = data

        # Navigate to parent
        for part in parts[:-1]:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return  # Path doesn't exist

        # Redact final field
        final_key = parts[-1]
        if isinstance(current, dict) and final_key in current:
            current[final_key] = "[REDACTED]"
