"""
NOESIS Memory Fortress - Circuit Breaker
=========================================

Prevents cascading failures by failing fast when backend is down.

Based on:
- Circuit Breaker Pattern (Michael Nygard, Release It!)
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    reset_timeout: float = 30.0
    half_open_max_calls: int = 3
    success_threshold: int = 2


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


class MemoryCircuitBreaker:
    """
    Circuit Breaker for Memory Operations.

    States:
    - CLOSED: Normal operation
    - OPEN: Backend down, reject requests
    - HALF_OPEN: Testing recovery

    Usage:
        breaker = MemoryCircuitBreaker(name="redis")
        result = await breaker.protected(operation, fallback)
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ) -> None:
        """
        Initialize circuit breaker.

        Args:
            name: Identifier for this breaker
            config: Configuration options
        """
        self.name = name
        self._config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Current circuit state."""
        return self._state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed."""
        return self._state == CircuitState.CLOSED

    async def can_execute(self) -> bool:
        """Check if request can be executed."""
        async with self._lock:
            if self._state == CircuitState.CLOSED:
                return True

            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    self._success_count = 0
                    logger.info(f"Circuit {self.name}: OPEN -> HALF_OPEN")
                    return True
                return False

            if self._half_open_calls < self._config.half_open_max_calls:
                self._half_open_calls += 1
                return True
            return False

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed."""
        if self._last_failure_time is None:
            return True
        elapsed = time.time() - self._last_failure_time
        return elapsed >= self._config.reset_timeout

    async def record_success(self) -> None:
        """Record successful operation."""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self._config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    logger.info(f"Circuit {self.name}: HALF_OPEN -> CLOSED")
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0

    async def record_failure(self) -> None:
        """Record failed operation."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning(f"Circuit {self.name}: HALF_OPEN -> OPEN")
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self._config.failure_threshold:
                    self._state = CircuitState.OPEN
                    logger.warning(f"Circuit {self.name}: CLOSED -> OPEN")

    async def protected(
        self,
        operation: Callable[[], T],
        fallback: Optional[Callable[[], T]] = None,
    ) -> T:
        """
        Execute operation with circuit breaker protection.

        Args:
            operation: Async operation to execute
            fallback: Optional fallback if circuit is open

        Returns:
            Operation result or fallback result

        Raises:
            CircuitOpenError: If circuit is open and no fallback
        """
        if not await self.can_execute():
            if fallback:
                logger.debug(f"Circuit {self.name} open, using fallback")
                return await fallback()
            raise CircuitOpenError(f"Circuit {self.name} is open")

        try:
            result = await operation()
            await self.record_success()
            return result
        except Exception as e:
            await self.record_failure()
            if fallback:
                logger.warning(f"Circuit {self.name} failed, using fallback: {e}")
                return await fallback()
            raise

    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status."""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure": (
                datetime.fromtimestamp(self._last_failure_time).isoformat()
                if self._last_failure_time else None
            ),
        }

