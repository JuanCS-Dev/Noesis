"""
Package refactored from sse_server.py.

Author: Claude Code + JuanCS-Dev
Refactored: 2025-12-03
"""

from __future__ import annotations

from ..sse_server_legacy import (
    ConnectionManager,
    GovernanceSSEServer,
    OperatorConnection,
    SSEEvent,
    decision_to_sse_data,
)

__all__ = [
    "SSEEvent",
    "OperatorConnection",
    "ConnectionManager",
    "GovernanceSSEServer",
    "decision_to_sse_data",
]
