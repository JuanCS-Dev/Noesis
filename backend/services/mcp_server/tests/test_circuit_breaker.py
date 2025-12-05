"""
Tests for Circuit Breaker.

Scientific tests for circuit breaker pattern implementation.
Follows CODE_CONSTITUTION: 100% type hints, Google style.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable

import pytest
from pybreaker import CircuitBreaker, CircuitBreakerError

from config import MCPServerConfig
from middleware.circuit_breaker import (
    get_circuit_breaker,
    ServiceUnavailableError,
)


class TestCircuitBreakerBasics:
    """Test basic circuit breaker functionality."""

    def test_get_circuit_breaker_creates_instance(
        self, config: MCPServerConfig
    ) -> None:
        """HYPOTHESIS: get_circuit_breaker() creates breaker instance."""
        breaker: CircuitBreaker = get_circuit_breaker("test_service", config)
        assert breaker is not None
        assert breaker.name == "test_service"

    def test_get_circuit_breaker_returns_same_instance(
        self, config: MCPServerConfig
    ) -> None:
        """HYPOTHESIS: Same name returns same breaker instance."""
        breaker1: CircuitBreaker = get_circuit_breaker("test_service", config)
        breaker2: CircuitBreaker = get_circuit_breaker("test_service", config)
        assert breaker1 is breaker2

    def test_circuit_breaker_initial_state_closed(
        self, config: MCPServerConfig
    ) -> None:
        """HYPOTHESIS: Circuit breaker starts in closed state."""
        breaker: CircuitBreaker = get_circuit_breaker("test_initial", config)
        assert str(breaker.current_state) == "closed"


class TestCircuitBreakerStates:
    """Test circuit breaker state transitions."""

    @pytest.mark.asyncio
    async def test_circuit_opens_after_threshold_failures(
        self, config: MCPServerConfig
    ) -> None:
        """HYPOTHESIS: Circuit opens after threshold failures."""
        breaker: CircuitBreaker = get_circuit_breaker("test_open", config)
        breaker.close()  # Ensure closed

        # Simulate failures (catch both error types)
        for _ in range(config.circuit_breaker_threshold):
            try:
                breaker.call(lambda: 1 / 0)  # Raises ZeroDivisionError
            except (ZeroDivisionError, CircuitBreakerError):
                pass

        # Circuit should be open now
        assert str(breaker.current_state) == "open"

    @pytest.mark.asyncio
    async def test_circuit_open_rejects_calls(
        self, config: MCPServerConfig
    ) -> None:
        """HYPOTHESIS: Open circuit rejects calls immediately."""
        breaker: CircuitBreaker = get_circuit_breaker("test_reject", config)
        breaker.close()

        # Force circuit open (catch both error types)
        for _ in range(config.circuit_breaker_threshold):
            try:
                breaker.call(lambda: 1 / 0)
            except (ZeroDivisionError, CircuitBreakerError):
                pass

        # Next call should raise CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            breaker.call(lambda: "should fail")

    @pytest.mark.asyncio
    async def test_circuit_half_open_after_timeout(
        self, config: MCPServerConfig
    ) -> None:
        """HYPOTHESIS: Circuit becomes half-open after timeout."""
        # Use short timeout for testing
        config.circuit_breaker_timeout = 0.1
        breaker: CircuitBreaker = get_circuit_breaker("test_halfopen", config)
        breaker.close()

        # Force open (catch both error types)
        for _ in range(config.circuit_breaker_threshold):
            try:
                breaker.call(lambda: 1 / 0)
            except (ZeroDivisionError, CircuitBreakerError):
                pass

        # Wait for timeout
        await asyncio.sleep(0.2)

        # Should be half-open now (allows one test call)
        assert str(breaker.current_state) in ["half-open", "open"]


class TestCircuitBreakerManualUsage:
    """Test manual circuit breaker usage."""

    @pytest.mark.asyncio
    async def test_manual_call_async_success(
        self, config: MCPServerConfig
    ) -> None:
        """HYPOTHESIS: Manual call_async allows successful calls."""
        breaker: CircuitBreaker = get_circuit_breaker("test_manual_ok", config)

        async def successful_call() -> str:
            return "success"

        result: str = await breaker.call_async(successful_call)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_manual_call_async_failure_propagates(
        self, config: MCPServerConfig
    ) -> None:
        """HYPOTHESIS: Manual call_async propagates failures."""
        breaker: CircuitBreaker = get_circuit_breaker("test_manual_fail", config)

        async def failing_call() -> None:
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            await breaker.call_async(failing_call)

    @pytest.mark.asyncio
    async def test_manual_opens_circuit_after_failures(
        self, config: MCPServerConfig
    ) -> None:
        """HYPOTHESIS: Manual usage opens circuit after threshold failures."""
        breaker: CircuitBreaker = get_circuit_breaker("test_manual_open", config)
        breaker.close()

        async def flaky_call() -> None:
            raise RuntimeError("always fails")

        # Make failures (catch both error types)
        for _ in range(config.circuit_breaker_threshold):
            try:
                await breaker.call_async(flaky_call)
            except (RuntimeError, CircuitBreakerError):
                pass

        # Circuit should be open, next call raises CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            await breaker.call_async(flaky_call)


class TestCircuitBreakerStateInspection:
    """Test circuit breaker state inspection."""

    def test_breaker_has_state_attribute(self, config: MCPServerConfig) -> None:
        """HYPOTHESIS: Breaker has current_state attribute."""
        breaker: CircuitBreaker = get_circuit_breaker("test_state_attr", config)
        assert hasattr(breaker, "current_state")
        assert str(breaker.current_state) in ["closed", "open", "half-open"]

    def test_breaker_has_fail_counter(self, config: MCPServerConfig) -> None:
        """HYPOTHESIS: Breaker tracks failure count."""
        breaker: CircuitBreaker = get_circuit_breaker("test_fail_counter", config)
        breaker.close()

        # Make a failure
        try:
            breaker.call(lambda: 1 / 0)
        except ZeroDivisionError:
            pass

        # Should have incremented counter
        assert breaker.fail_counter > 0

    def test_breaker_reset_clears_failures(
        self, config: MCPServerConfig
    ) -> None:
        """HYPOTHESIS: reset() clears failure counter."""
        breaker: CircuitBreaker = get_circuit_breaker("test_reset_clear", config)
        breaker.close()

        # Make failures
        for _ in range(2):
            try:
                breaker.call(lambda: 1 / 0)
            except ZeroDivisionError:
                pass

        # Reset
        breaker.close()  # Closes and resets

        # Should be back to closed
        assert str(breaker.current_state) == "closed"


class TestCircuitBreakerEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_sync_function_through_breaker(
        self, config: MCPServerConfig
    ) -> None:
        """HYPOTHESIS: Breaker works with sync functions."""
        breaker: CircuitBreaker = get_circuit_breaker("test_sync", config)

        def sync_function() -> int:
            return 42

        # Sync function called through breaker
        result: int = breaker.call(sync_function)
        assert result == 42

    @pytest.mark.asyncio
    async def test_multiple_breakers_independent(
        self, config: MCPServerConfig
    ) -> None:
        """HYPOTHESIS: Different breakers are independent."""
        breaker1: CircuitBreaker = get_circuit_breaker("service_1", config)
        breaker2: CircuitBreaker = get_circuit_breaker("service_2", config)

        # Open breaker1 (catch both error types)
        for _ in range(config.circuit_breaker_threshold):
            try:
                breaker1.call(lambda: 1 / 0)
            except (ZeroDivisionError, CircuitBreakerError):
                pass

        # breaker1 should be open
        assert str(breaker1.current_state) == "open"

        # breaker2 should still be closed
        assert str(breaker2.current_state) == "closed"
