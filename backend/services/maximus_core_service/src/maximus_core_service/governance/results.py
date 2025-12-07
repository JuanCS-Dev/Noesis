"""
Governance Result Models.

Contains result structures for governance operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GovernanceResult:
    """Result of governance operation."""

    success: bool = True
    message: str = ""
    entity_id: str | None = None  # ID of created/updated entity
    entity_type: str = ""  # policy, member, meeting, etc.
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "message": self.message,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "warnings": self.warnings,
            "errors": self.errors,
            "metadata": self.metadata,
        }
