"""
Soul Configuration Module
=========================

Manages the NOESIS soul configuration - the ethical and cognitive identity
that guides all exocortex operations.

This module provides:
- Pydantic models for soul configuration validation
- YAML loader for soul_config.yaml
- Integration utilities for other exocortex modules
"""

from .models import (
    SoulConfiguration,
    SoulIdentity,
    SoulValue,
    BiasEntry,
    ProtocolConfig,
    MetacognitionConfig,
)
from .loader import SoulLoader

__all__ = [
    "SoulConfiguration",
    "SoulIdentity",
    "SoulValue",
    "BiasEntry",
    "ProtocolConfig",
    "MetacognitionConfig",
    "SoulLoader",
]
