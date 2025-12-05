"""
Tests for Streaming Bridge.

Scientific tests for StreamingBridge bidirectional streaming.
Follows CODE_CONSTITUTION: 100% type hints, Google style.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Coroutine, Dict, List, Optional

import pytest

from streaming.bridge import MessageType, StreamingBridge, StreamingMessage


class TestStreamingMessage:
    """Test StreamingMessage dataclass."""

    def test_message_has_required_fields(self) -> None:
        """HYPOTHESIS: StreamingMessage has all required fields."""
        msg: StreamingMessage = StreamingMessage(
            type=MessageType.PROGRESS,
            data={"progress": 50},
            sequence=1,
        )

        assert msg.type == MessageType.PROGRESS
        assert msg.data == {"progress": 50}
        assert msg.sequence == 1
        assert msg.timestamp is not None
        assert msg.message_id is not None

    def test_message_to_dict_serializes_correctly(self) -> None:
        """HYPOTHESIS: to_dict produces valid dictionary."""
        msg: StreamingMessage = StreamingMessage(
            type=MessageType.RESULT,
            data={"result": "ok"},
            sequence=42,
        )

        result: Dict[str, Any] = msg.to_dict()

        assert result["type"] == "result"
        assert result["data"] == {"result": "ok"}
        assert result["sequence"] == 42
        assert "timestamp" in result
        assert "message_id" in result


class TestMessageType:
    """Test MessageType enum."""

    def test_all_types_exist(self) -> None:
        """HYPOTHESIS: All required message types exist."""
        assert MessageType.REQUEST == "request"
        assert MessageType.PROGRESS == "progress"
        assert MessageType.RESULT == "result"
        assert MessageType.ERROR == "error"


class TestStreamingBridge:
    """Test StreamingBridge streaming functionality."""

    @pytest.fixture
    def bridge(self) -> StreamingBridge:
        """Create fresh bridge for each test."""
        return StreamingBridge(timeout=5.0)

    @pytest.mark.asyncio
    async def test_stream_operation_reports_progress(
        self, bridge: StreamingBridge
    ) -> None:
        """HYPOTHESIS: stream_operation yields progress updates."""
        progress_updates: List[float] = []

        async def handler(
            params: Dict[str, Any],
            progress_cb: Callable[..., Coroutine[Any, Any, None]],
        ) -> Dict[str, str]:
            await progress_cb(0, 100, "Starting")
            await progress_cb(50, 100, "Halfway")
            await progress_cb(100, 100, "Done")
            return {"status": "ok"}

        async for msg in bridge.stream_operation("test", {}, handler):
            if msg.type == MessageType.PROGRESS:
                progress_updates.append(msg.data["percentage"])

        assert len(progress_updates) >= 3
        assert 0.0 in progress_updates
        assert 50.0 in progress_updates
        assert 100.0 in progress_updates

    @pytest.mark.asyncio
    async def test_stream_operation_returns_result(
        self, bridge: StreamingBridge
    ) -> None:
        """HYPOTHESIS: stream_operation yields final result."""
        result_received: Optional[Dict[str, Any]] = None

        async def handler(
            params: Dict[str, Any],
            progress_cb: Callable[..., Coroutine[Any, Any, None]],
        ) -> Dict[str, int]:
            return {"value": 42}

        async for msg in bridge.stream_operation("test", {}, handler):
            if msg.type == MessageType.RESULT:
                result_received = msg.data

        assert result_received == {"value": 42}

    @pytest.mark.asyncio
    async def test_stream_operation_handles_errors(
        self, bridge: StreamingBridge
    ) -> None:
        """HYPOTHESIS: stream_operation yields error on exception."""
        error_received: Optional[Dict[str, Any]] = None

        async def handler(
            params: Dict[str, Any],
            progress_cb: Callable[..., Coroutine[Any, Any, None]],
        ) -> Dict[str, str]:
            raise ValueError("Test error")

        async for msg in bridge.stream_operation("test", {}, handler):
            if msg.type == MessageType.ERROR:
                error_received = msg.data

        assert error_received is not None
        assert "Test error" in error_received["error"]

    @pytest.mark.asyncio
    async def test_stream_operation_respects_timeout(
        self, bridge: StreamingBridge
    ) -> None:
        """HYPOTHESIS: stream_operation times out correctly."""
        bridge.timeout = 0.1  # 100ms timeout
        error_received: Optional[Dict[str, Any]] = None

        async def handler(
            params: Dict[str, Any],
            progress_cb: Callable[..., Coroutine[Any, Any, None]],
        ) -> Dict[str, str]:
            await asyncio.sleep(10)  # Sleep longer than timeout
            return {"status": "ok"}

        async for msg in bridge.stream_operation("test", {}, handler):
            if msg.type == MessageType.ERROR:
                error_received = msg.data

        assert error_received is not None
        assert "timed out" in error_received["error"]

    @pytest.mark.asyncio
    async def test_stream_operation_passes_params(
        self, bridge: StreamingBridge
    ) -> None:
        """HYPOTHESIS: stream_operation passes params to handler."""
        received_params: Optional[Dict[str, Any]] = None

        async def handler(
            params: Dict[str, Any],
            progress_cb: Callable[..., Coroutine[Any, Any, None]],
        ) -> Dict[str, str]:
            nonlocal received_params
            received_params = params
            return {"status": "ok"}

        async for _ in bridge.stream_operation("test", {"x": 1, "y": 2}, handler):
            pass

        assert received_params == {"x": 1, "y": 2}

    @pytest.mark.asyncio
    async def test_sequence_numbers_increment(
        self, bridge: StreamingBridge
    ) -> None:
        """HYPOTHESIS: Each operation gets unique sequence number."""
        sequences: List[int] = []

        async def handler(
            params: Dict[str, Any],
            progress_cb: Callable[..., Coroutine[Any, Any, None]],
        ) -> Dict[str, str]:
            return {"status": "ok"}

        for _ in range(3):
            async for msg in bridge.stream_operation("test", {}, handler):
                if msg.type == MessageType.RESULT:
                    sequences.append(msg.sequence)

        assert len(sequences) == 3
        assert sequences[0] < sequences[1] < sequences[2]

    @pytest.mark.asyncio
    async def test_progress_message_includes_percentage(
        self, bridge: StreamingBridge
    ) -> None:
        """HYPOTHESIS: Progress messages include calculated percentage."""
        progress_msg: Optional[StreamingMessage] = None

        async def handler(
            params: Dict[str, Any],
            progress_cb: Callable[..., Coroutine[Any, Any, None]],
        ) -> Dict[str, str]:
            await progress_cb(25, 100, "Quarter done")
            return {"status": "ok"}

        async for msg in bridge.stream_operation("test", {}, handler):
            if msg.type == MessageType.PROGRESS and msg.data.get("progress") == 25:
                progress_msg = msg

        assert progress_msg is not None
        assert progress_msg.data["percentage"] == 25.0
        assert progress_msg.data["message"] == "Quarter done"

    @pytest.mark.asyncio
    async def test_result_terminates_stream(
        self, bridge: StreamingBridge
    ) -> None:
        """HYPOTHESIS: Result message terminates stream iteration."""
        message_count: int = 0

        async def handler(
            params: Dict[str, Any],
            progress_cb: Callable[..., Coroutine[Any, Any, None]],
        ) -> Dict[str, str]:
            await progress_cb(50, 100)
            return {"status": "ok"}

        async for msg in bridge.stream_operation("test", {}, handler):
            message_count += 1
            if message_count > 10:
                break  # Safety limit

        assert message_count <= 5  # Progress + Result shouldn't be many

    @pytest.mark.asyncio
    async def test_error_terminates_stream(
        self, bridge: StreamingBridge
    ) -> None:
        """HYPOTHESIS: Error message terminates stream iteration."""
        message_count: int = 0

        async def handler(
            params: Dict[str, Any],
            progress_cb: Callable[..., Coroutine[Any, Any, None]],
        ) -> Dict[str, str]:
            raise RuntimeError("Failure")

        async for msg in bridge.stream_operation("test", {}, handler):
            message_count += 1
            if message_count > 10:
                break  # Safety limit

        assert message_count <= 5  # Progress + Error shouldn't be many
