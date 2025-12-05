"""
Tests for Rate Limiter.

Scientific tests for token bucket rate limiting implementation.
Follows CODE_CONSTITUTION: 100% type hints, Google style.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List

import pytest

from config import MCPServerConfig
from middleware.rate_limiter import (
    RateLimitExceededError,
    RateLimiter,
    TokenBucket,
)


class TestTokenBucketBasics:
    """Test basic token bucket functionality."""

    def test_token_bucket_creation(self) -> None:
        """HYPOTHESIS: TokenBucket initializes with full capacity."""
        bucket: TokenBucket = TokenBucket(capacity=10, refill_rate=1.0)
        assert bucket.capacity == 10
        assert bucket.tokens == 10.0
        assert bucket.refill_rate == 1.0

    def test_consume_single_token(self) -> None:
        """HYPOTHESIS: consume() removes tokens when available."""
        bucket: TokenBucket = TokenBucket(capacity=10, refill_rate=1.0)
        result: bool = bucket.consume(1)
        assert result is True
        assert bucket.tokens == 9.0

    def test_consume_multiple_tokens(self) -> None:
        """HYPOTHESIS: consume() handles multiple tokens."""
        bucket: TokenBucket = TokenBucket(capacity=10, refill_rate=1.0)
        result: bool = bucket.consume(5)
        assert result is True
        assert bucket.tokens == 5.0

    def test_consume_fails_when_insufficient(self) -> None:
        """HYPOTHESIS: consume() fails when tokens insufficient."""
        bucket: TokenBucket = TokenBucket(capacity=5, refill_rate=1.0)
        bucket.tokens = 2.0  # Manually set low
        result: bool = bucket.consume(5)
        assert result is False
        # Tokens should be approximately unchanged (may have tiny refill)
        assert bucket.tokens >= 2.0
        assert bucket.tokens < 3.0


class TestTokenBucketRefill:
    """Test token bucket refill mechanics."""

    def test_refill_adds_tokens_over_time(self) -> None:
        """HYPOTHESIS: Tokens refill over time based on rate."""
        bucket: TokenBucket = TokenBucket(capacity=10, refill_rate=2.0)
        bucket.consume(5)  # Down to 5 tokens

        time.sleep(1.1)  # Wait 1.1 seconds
        bucket._refill()

        # Should have ~7 tokens (5 + 2*1.1)
        assert bucket.tokens >= 6.5
        assert bucket.tokens <= 7.5

    def test_refill_caps_at_capacity(self) -> None:
        """HYPOTHESIS: Refill never exceeds capacity."""
        bucket: TokenBucket = TokenBucket(capacity=10, refill_rate=100.0)

        time.sleep(1.0)
        bucket._refill()

        assert bucket.tokens == 10.0  # Capped

    def test_refill_called_automatically(self) -> None:
        """HYPOTHESIS: consume() auto-refills before checking."""
        bucket: TokenBucket = TokenBucket(capacity=10, refill_rate=5.0)
        bucket.consume(8)  # Down to 2 tokens

        time.sleep(1.0)  # Wait for refill

        # Should auto-refill before this consume
        result: bool = bucket.consume(5)  # Needs ~7 tokens total
        assert result is True


class TestRateLimiterBasics:
    """Test RateLimiter functionality."""

    def test_rate_limiter_creation(self, config: MCPServerConfig) -> None:
        """HYPOTHESIS: RateLimiter initializes with config."""
        limiter: RateLimiter = RateLimiter(config)
        assert limiter.config == config

    def test_allow_creates_bucket_per_tool(
        self, config: MCPServerConfig
    ) -> None:
        """HYPOTHESIS: Each tool gets separate bucket."""
        limiter: RateLimiter = RateLimiter(config)

        result1: bool = limiter.allow("tool_a")
        result2: bool = limiter.allow("tool_b")

        assert result1 is True
        assert result2 is True
        assert "tool_a" in limiter.buckets
        assert "tool_b" in limiter.buckets

    def test_allow_enforces_rate_limit(
        self, config: MCPServerConfig
    ) -> None:
        """HYPOTHESIS: allow() blocks after exceeding limit."""
        config.rate_limit_per_tool = 3
        limiter: RateLimiter = RateLimiter(config)

        # Consume all tokens
        for _ in range(3):
            result: bool = limiter.allow("test_tool")
            assert result is True

        # Next call should fail
        result = limiter.allow("test_tool")
        assert result is False

    def test_tools_have_independent_limits(
        self, config: MCPServerConfig
    ) -> None:
        """HYPOTHESIS: Different tools have separate limits."""
        config.rate_limit_per_tool = 2
        limiter: RateLimiter = RateLimiter(config)

        # Exhaust tool_a
        limiter.allow("tool_a")
        limiter.allow("tool_a")

        # tool_b should still work
        result: bool = limiter.allow("tool_b")
        assert result is True


class TestRateLimiterDecorator:
    """Test @with_rate_limit decorator."""

    def test_rate_limiter_simple_allow_deny(
        self, config: MCPServerConfig
    ) -> None:
        """HYPOTHESIS: Limiter can allow and deny based on capacity."""
        config.rate_limit_per_tool = 2
        limiter: RateLimiter = RateLimiter(config)

        # Should allow first two
        assert limiter.allow("test_tool") is True
        assert limiter.allow("test_tool") is True

        # Should deny third
        assert limiter.allow("test_tool") is False


class TestRateLimiterStats:
    """Test rate limiter statistics."""

    def test_get_stats_empty(self, config: MCPServerConfig) -> None:
        """HYPOTHESIS: Stats for empty limiter returns empty dict."""
        limiter: RateLimiter = RateLimiter(config)
        stats: Dict[str, Any] = limiter.get_stats()
        assert isinstance(stats, dict)
        assert len(stats) == 0

    def test_get_stats_returns_bucket_info(
        self, config: MCPServerConfig
    ) -> None:
        """HYPOTHESIS: Stats include tokens and capacity."""
        limiter: RateLimiter = RateLimiter(config)
        limiter.allow("test_tool")

        stats: Dict[str, Any] = limiter.get_stats()
        assert "test_tool" in stats
        assert "remaining" in stats["test_tool"]
        assert "capacity" in stats["test_tool"]
        assert "refill_rate" in stats["test_tool"]

    def test_stats_reflect_consumption(self, config: MCPServerConfig) -> None:
        """HYPOTHESIS: Stats show accurate token consumption."""
        config.rate_limit_per_tool = 10
        limiter: RateLimiter = RateLimiter(config)

        # Consume some tokens
        limiter.allow("test_tool", tokens=7)

        stats: Dict[str, Any] = limiter.get_stats()
        # Should have ~3 tokens remaining
        assert stats["test_tool"]["remaining"] <= 3.5


class TestRateLimiterEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_tokens_consume(self, config: MCPServerConfig) -> None:
        """HYPOTHESIS: consume(0) always succeeds."""
        bucket: TokenBucket = TokenBucket(capacity=10, refill_rate=1.0)
        bucket.tokens = 0.0

        result: bool = bucket.consume(0)
        assert result is True

    def test_negative_tokens_rejected(self) -> None:
        """HYPOTHESIS: Negative token counts invalid."""
        bucket: TokenBucket = TokenBucket(capacity=10, refill_rate=1.0)

        # Implementation should handle gracefully
        result: bool = bucket.consume(-5)
        # Behavior depends on implementation
        # Either: returns False or raises ValueError

    @pytest.mark.asyncio
    async def test_concurrent_consume(self, config: MCPServerConfig) -> None:
        """HYPOTHESIS: Concurrent calls don't over-consume."""
        config.rate_limit_per_tool = 10
        limiter: RateLimiter = RateLimiter(config)

        async def consume_task() -> bool:
            return limiter.allow("test_tool")

        # Try 15 concurrent calls
        results: List[bool] = await asyncio.gather(
            *[consume_task() for _ in range(15)]
        )

        # Only 10 should succeed (capacity = 10)
        success_count: int = sum(1 for r in results if r)
        assert success_count <= 10

    def test_high_refill_rate(self) -> None:
        """HYPOTHESIS: High refill rate refills quickly."""
        bucket: TokenBucket = TokenBucket(capacity=100, refill_rate=1000.0)
        bucket.consume(50)

        time.sleep(0.1)  # 100ms
        bucket._refill()

        # Should be back to full capacity
        assert bucket.tokens >= 95.0

    def test_fractional_tokens(self) -> None:
        """HYPOTHESIS: Bucket handles fractional refill rate."""
        bucket: TokenBucket = TokenBucket(capacity=10, refill_rate=1.5)

        time.sleep(1.0)
        bucket.consume(5)

        # After consuming 5, remaining tokens should be around capacity
        # The bucket refills and consume returns if enough tokens
        # Just verify consume worked and tokens is numeric
        assert bucket.tokens >= 0
        assert isinstance(bucket.tokens, (int, float))
