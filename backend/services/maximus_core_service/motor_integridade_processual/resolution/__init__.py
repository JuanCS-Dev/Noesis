"""Conflict Resolution Engine."""

from __future__ import annotations


from motor_integridade_processual.resolution.conflict_resolver import ConflictResolver
from motor_integridade_processual.resolution.rules import ResolutionRules

__all__ = ["ConflictResolver", "ResolutionRules"]
