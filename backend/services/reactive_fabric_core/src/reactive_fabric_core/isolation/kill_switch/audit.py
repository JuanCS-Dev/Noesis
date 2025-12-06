"""
Audit Logging for Kill Switch.

Records all kill switch events for compliance and forensics.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class AuditMixin:
    """Mixin providing audit logging functionality."""

    _armed: bool
    _audit_file: Path

    def _audit_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """
        Record audit event.

        Args:
            event_type: Type of event (ARMED, DISARMED, ACTIVATED, etc.)
            details: Event details dictionary
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "armed": self._armed,
            "details": details,
        }

        try:
            self._audit_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._audit_file, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            logger.error("Failed to write audit log: %s", e)
