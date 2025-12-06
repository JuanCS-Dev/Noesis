"""
Streaming Module
================

Bidirectional streaming support for MCP tools.

Follows CODE_CONSTITUTION: Simplicity at Scale.
"""

from __future__ import annotations

from mcp_server.streaming.bridge import StreamingBridge, StreamingMessage

__all__ = ["StreamingBridge", "StreamingMessage"]
