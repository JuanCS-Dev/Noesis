"""
Deception Engine for Reactive Fabric.

Creates and manages honeytokens, decoys, and deceptive elements.
Phase 1: PASSIVE deception only - monitoring without active engagement.
"""

from __future__ import annotations


from .deception_engine import (
    BreadcrumbTrail,
    DeceptionConfig,
    DeceptionEngine,
    DeceptionEvent,
    DeceptionType,
    DecoySystem,
    Honeytoken,
    HoneytokenGenerator,
    TokenType,
    TrapDocument,
)

__all__ = [
    "BreadcrumbTrail",
    "DeceptionConfig",
    "DeceptionEngine",
    "DeceptionEvent",
    "DeceptionType",
    "DecoySystem",
    "Honeytoken",
    "HoneytokenGenerator",
    "TokenType",
    "TrapDocument",
]