"""Models for compliance module."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ComplianceResult:
    """Compliance check result."""
    
    compliant: bool = True
    findings: list[str] = field(default_factory=list)
    score: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
