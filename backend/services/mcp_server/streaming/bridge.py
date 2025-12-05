"""
Streaming Bridge
================

Bidirectional streaming for real-time MCP communication.

Based on: Google ADK LiveRequestQueue pattern (2025).
Provides progress reporting and streaming responses for long-running operations.

Follows CODE_CONSTITUTION: Simplicity at Scale, Clarity Over Cleverness.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Dict, Optional
from uuid import uuid4


logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Streaming message types."""

    REQUEST = "request"
    PROGRESS = "progress"
    RESULT = "result"
    ERROR = "error"


@dataclass
class StreamingMessage:  # pylint: disable=too-few-public-methods
    """
    Message for streaming communication.

    Attributes:
        type: Message type (request, progress, result, error)
        data: Message payload
        sequence: Message sequence number for ordering
        timestamp: Creation timestamp
        message_id: Unique message identifier
    """

    type: MessageType
    data: Dict[str, Any]
    sequence: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    message_id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "type": self.type.value,
            "data": self.data,
            "sequence": self.sequence,
            "timestamp": self.timestamp.isoformat(),
            "message_id": self.message_id,
        }


class StreamingBridge:  # pylint: disable=too-few-public-methods
    """
    Bidirectional streaming bridge for MCP tools.

    Enables real-time progress updates and streaming responses
    for long-running operations like tribunal evaluation and
    memory consolidation.

    Based on: Google ADK LiveRequestQueue pattern.

    Example:
        >>> bridge = StreamingBridge()
        >>> async for msg in bridge.stream_operation("consolidate", {"threshold": 0.8}):
        ...     if msg.type == MessageType.PROGRESS:
        ...         print(f"Progress: {msg.data.get('percentage', 0):.0f}%")
        ...     elif msg.type == MessageType.RESULT:
        ...         print(f"Result: {msg.data}")
    """

    def __init__(self, timeout: float = 120.0) -> None:
        """
        Initialize streaming bridge.

        Args:
            timeout: Operation timeout in seconds (default: 120s)
        """
        self.timeout = timeout
        self._response_queues: Dict[int, asyncio.Queue[StreamingMessage]] = {}
        self._sequence = 0
        self._lock = asyncio.Lock()

    async def stream_operation(
        self,
        operation: str,
        params: Dict[str, Any],
        handler: Any,
    ) -> AsyncIterator[StreamingMessage]:
        """
        Stream operation execution with progress updates.

        Args:
            operation: Operation name
            params: Operation parameters
            handler: Async handler function that accepts (params, progress_callback)

        Yields:
            StreamingMessage with progress/result updates

        Example:
            >>> async def my_handler(params, progress_cb):
            ...     await progress_cb(50, 100, "Halfway done")
            ...     return {"status": "ok"}
            >>> async for msg in bridge.stream_operation("test", {}, my_handler):
            ...     print(msg.type, msg.data)
        """
        async with self._lock:
            self._sequence += 1
            seq = self._sequence

        response_queue: asyncio.Queue[StreamingMessage] = asyncio.Queue()
        self._response_queues[seq] = response_queue

        async def progress_callback(
            progress: int,
            total: int = 100,
            message: Optional[str] = None,
        ) -> None:
            """Report progress for streaming operation."""
            await self._report_progress(seq, progress, total, message)

        try:
            operation_task = asyncio.create_task(
                self._execute_with_progress(
                    seq, operation, params, handler, progress_callback
                )
            )

            async with asyncio.timeout(self.timeout):
                while True:
                    response = await response_queue.get()
                    yield response

                    if response.type in (MessageType.RESULT, MessageType.ERROR):
                        break

            await operation_task

        except asyncio.TimeoutError:
            logger.error("Operation %s timed out after %.1fs", operation, self.timeout)
            yield StreamingMessage(
                type=MessageType.ERROR,
                data={"error": f"Operation timed out after {self.timeout}s"},
                sequence=seq,
            )
        finally:
            self._response_queues.pop(seq, None)

    async def _execute_with_progress(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        sequence: int,
        operation: str,
        params: Dict[str, Any],
        handler: Any,
        progress_callback: Any,
    ) -> None:
        """Execute handler and send result/error to queue."""
        try:
            await self._report_progress(sequence, 0, 100, f"Starting {operation}")

            result = await handler(params, progress_callback)

            await self._send_result(sequence, result)

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Operation %s failed: %s", operation, e, exc_info=True)
            await self._send_error(sequence, str(e))

    async def _report_progress(
        self,
        sequence: int,
        progress: int,
        total: int = 100,
        message: Optional[str] = None,
    ) -> None:
        """Report progress for a streaming operation."""
        queue = self._response_queues.get(sequence)
        if not queue:
            return

        percentage = (progress / total) * 100 if total > 0 else 0
        await queue.put(
            StreamingMessage(
                type=MessageType.PROGRESS,
                data={
                    "progress": progress,
                    "total": total,
                    "percentage": percentage,
                    "message": message,
                },
                sequence=sequence,
            )
        )
        logger.debug(
            "Progress %d/%d (%.0f%%): %s", progress, total, percentage, message or ""
        )

    async def _send_result(
        self,
        sequence: int,
        result: Dict[str, Any],
    ) -> None:
        """Send final result for a streaming operation."""
        queue = self._response_queues.get(sequence)
        if not queue:
            return

        await queue.put(
            StreamingMessage(
                type=MessageType.RESULT,
                data=result,
                sequence=sequence,
            )
        )
        logger.debug("Result sent for sequence %d", sequence)

    async def _send_error(
        self,
        sequence: int,
        error: str,
    ) -> None:
        """Send error for a streaming operation."""
        queue = self._response_queues.get(sequence)
        if not queue:
            return

        await queue.put(
            StreamingMessage(
                type=MessageType.ERROR,
                data={"error": error},
                sequence=sequence,
            )
        )
        logger.debug("Error sent for sequence %d: %s", sequence, error)
