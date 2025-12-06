"""Application State Management - Shared state for routers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ethical_audit_service.database import EthicalAuditDatabase
    from slowapi import Limiter

# Global state
_db: "EthicalAuditDatabase | None" = None
_limiter: "Limiter | None" = None
_app_state: dict[str, Any] = {}


def set_db(db: "EthicalAuditDatabase") -> None:
    """Set the database instance."""
    global _db  # noqa: PLW0603
    _db = db


def get_db() -> "EthicalAuditDatabase | None":
    """Get the database instance."""
    return _db


def set_limiter(limiter: "Limiter") -> None:
    """Set the rate limiter instance."""
    global _limiter  # noqa: PLW0603
    _limiter = limiter


def get_limiter() -> "Limiter | None":
    """Get the rate limiter instance."""
    return _limiter


def get_app_state() -> dict[str, Any]:
    """Get the application state dictionary."""
    return _app_state


def set_app_state_value(key: str, value: Any) -> None:
    """Set a value in the application state."""
    _app_state[key] = value


def get_app_state_value(key: str, default: Any = None) -> Any:
    """Get a value from the application state."""
    return _app_state.get(key, default)
