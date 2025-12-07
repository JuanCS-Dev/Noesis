"""Conflict Resolution Engine."""

from __future__ import annotations


from maximus_core_service.motor_integridade_processual.resolution.conflict_resolver import ConflictResolver
from maximus_core_service.motor_integridade_processual.resolution.rules import ResolutionRules

__all__ = ["ConflictResolver", "ResolutionRules"]
