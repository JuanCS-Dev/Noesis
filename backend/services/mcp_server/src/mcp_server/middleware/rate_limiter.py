"""
Rate Limiter Middleware
=======================

Implements token bucket rate limiting per tool.

Follows CODE_CONSTITUTION: Safety First.
"""

from __future__ import annotations

import time
from typing import Dict

from mcp_server.config import MCPServerConfig


class TokenBucket:
    """Token bucket for rate limiting.

    Implements classic token bucket algorithm:
    - Bucket starts full with N tokens
    - Each request consumes 1 token
    - Tokens refill at constant rate
    - If bucket empty, request is rejected

    Example:
        >>> bucket = TokenBucket(capacity=100, refill_rate=10)
        >>> if bucket.consume():
        ...     # Request allowed
        ...     process_request()
    """

    def __init__(self, capacity: int, refill_rate: float):
        """Initialize token bucket.

        Args:
            capacity: Maximum tokens (burst size)
            refill_rate: Tokens per second refill rate
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_update = time.time()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update

        # Add tokens based on elapsed time
        self.tokens = min(
            self.capacity, self.tokens + elapsed * self.refill_rate
        )
        self.last_update = now

    def consume(self, tokens: int = 1) -> bool:
        """Attempt to consume tokens.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens available, False otherwise
        """
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def peek(self) -> float:
        """Check current token count without consuming.

        Returns:
            Current number of tokens available
        """
        self._refill()
        return self.tokens


class RateLimiter:
    """Rate limiter for MCP tools.

    Maintains separate token bucket for each tool.

    Example:
        >>> limiter = RateLimiter(config)
        >>> if limiter.allow("tribunal_evaluate"):
        ...     # Request allowed
        ...     call_tool()
    """

    def __init__(self, config: MCPServerConfig):
        """Initialize rate limiter.

        Args:
            config: Service configuration
        """
        self.config = config
        self.buckets: Dict[str, TokenBucket] = {}

        # Calculate refill rate (tokens per second)
        # Example: 100 requests per 60 seconds = 1.67 requests/sec
        self.refill_rate = config.rate_limit_per_tool / config.rate_limit_window

    def _get_bucket(self, tool_name: str) -> TokenBucket:
        """Get or create token bucket for tool.

        Args:
            tool_name: Name of MCP tool

        Returns:
            TokenBucket instance
        """
        if tool_name not in self.buckets:
            self.buckets[tool_name] = TokenBucket(
                capacity=self.config.rate_limit_per_tool,
                refill_rate=self.refill_rate,
            )
        return self.buckets[tool_name]

    def allow(self, tool_name: str, tokens: int = 1) -> bool:
        """Check if request is allowed.

        Args:
            tool_name: Name of MCP tool
            tokens: Tokens to consume (default: 1)

        Returns:
            True if allowed, False if rate limited

        Example:
            >>> if limiter.allow("tribunal_evaluate"):
            ...     result = await tool()
            ... else:
            ...     raise RateLimitExceededError()
        """
        bucket = self._get_bucket(tool_name)
        return bucket.consume(tokens)

    def get_remaining(self, tool_name: str) -> float:
        """Get remaining tokens for tool.

        Args:
            tool_name: Name of MCP tool

        Returns:
            Number of tokens remaining

        Example:
            >>> remaining = limiter.get_remaining("tribunal_evaluate")
            >>> print(f"{remaining} requests remaining")
        """
        bucket = self._get_bucket(tool_name)
        return bucket.peek()

    def get_stats(self) -> Dict[str, Dict[str, float]]:
        """Get rate limit stats for all tools.

        Returns:
            Dict mapping tool name to stats

        Example:
            >>> stats = limiter.get_stats()
            >>> stats["tribunal_evaluate"]["remaining"]
            85.5
        """
        return {
            tool_name: {
                "remaining": bucket.peek(),
                "capacity": bucket.capacity,
                "refill_rate": bucket.refill_rate,
            }
            for tool_name, bucket in self.buckets.items()
        }

    def reset(self, tool_name: Optional[str] = None) -> None:
        """Reset rate limiter.

        Args:
            tool_name: Reset specific tool (None = reset all)
        """
        if tool_name:
            if tool_name in self.buckets:
                bucket = self.buckets[tool_name]
                bucket.tokens = float(bucket.capacity)
                bucket.last_update = time.time()
        else:
            # Reset all buckets
            for bucket in self.buckets.values():
                bucket.tokens = float(bucket.capacity)
                bucket.last_update = time.time()


class RateLimitExceededError(Exception):
    """Raised when rate limit is exceeded."""

    pass


# Import Optional at the end
from typing import Optional
