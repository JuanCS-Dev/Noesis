"""Shim for backward compatibility."""
from .storage_pkg import (
    FLModelRegistry,
    FLRoundHistory,
    ModelVersion,
    RestrictedUnpickler,
    safe_pickle_load,
)

__all__ = [
    "RestrictedUnpickler",
    "ModelVersion",
    "FLModelRegistry",
    "FLRoundHistory",
    "safe_pickle_load",
]
