"""
Circuit Breaker Middleware
==========================

Implements circuit breaker pattern for resilience.

Follows CODE_CONSTITUTION: Safety First, Antifragilidade.
"""

from __future__ import annotations

import functools
from typing import Any, Callable, Optional

from pybreaker import CircuitBreaker, CircuitBreakerError

from mcp_server.config import MCPServerConfig

# Global registry of circuit breakers (one per service)
_CIRCUIT_BREAKERS: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str, config: MCPServerConfig
) -> CircuitBreaker:
    """Get or create circuit breaker for a service.

    Args:
        name: Unique name for this circuit
        config: Service configuration

    Returns:
        CircuitBreaker instance

    Example:
        >>> breaker = get_circuit_breaker("tribunal", config)
        >>> breaker.call(some_function, args)
    """
    if name not in _CIRCUIT_BREAKERS:
        _CIRCUIT_BREAKERS[name] = CircuitBreaker(
            fail_max=config.circuit_breaker_threshold,
            reset_timeout=config.circuit_breaker_timeout,
            name=name,
        )
    return _CIRCUIT_BREAKERS[name]


def with_circuit_breaker(
    service_name: str,
    failure_threshold: Optional[int] = None,
    timeout: Optional[float] = None,
) -> Callable:
    """Decorator to wrap function with circuit breaker.

    Args:
        service_name: Name of service being called
        failure_threshold: Override config threshold (optional)
        timeout: Override config timeout (optional)

    Returns:
        Decorated function

    Example:
        >>> @with_circuit_breaker("tribunal", failure_threshold=5)
        ... async def call_tribunal():
        ...     return await tribunal.evaluate(log)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Get config from kwargs or use defaults
            config = kwargs.get("config")
            if not config:
                from config import get_config

                config = get_config()

            # Get or create breaker with overrides if specified
            if failure_threshold or timeout:
                # Create custom config for this breaker
                custom_config = MCPServerConfig(
                    **{
                        **config.model_dump(),
                        "circuit_breaker_threshold": failure_threshold or config.circuit_breaker_threshold,
                        "circuit_breaker_timeout": timeout or config.circuit_breaker_timeout,
                    }
                )
                breaker = get_circuit_breaker(f"{service_name}_custom", custom_config)
            else:
                breaker = get_circuit_breaker(service_name, config)

            try:
                # Call function through breaker
                if asyncio.iscoroutinefunction(func):
                    result = await breaker.call_async(func, *args, **kwargs)
                else:
                    result = breaker.call(func, *args, **kwargs)
                return result
            except CircuitBreakerError as e:
                # Circuit is open - service unavailable
                raise ServiceUnavailableError(
                    f"Circuit breaker open for {service_name}: {e}"
                )

        return wrapper

    return decorator


class ServiceUnavailableError(Exception):
    """Raised when service is unavailable due to circuit breaker."""

    pass


def get_breaker_stats() -> dict[str, dict[str, Any]]:
    """Get statistics for all circuit breakers.

    Returns:
        Dict mapping service name to stats

    Example:
        >>> stats = get_breaker_stats()
        >>> stats["tribunal"]["state"]
        'closed'
    """
    return {
        name: {
            "state": str(breaker.current_state),
            "fail_counter": breaker.fail_counter,
            "last_failure": getattr(breaker, "last_failure", None),
        }
        for name, breaker in _CIRCUIT_BREAKERS.items()
    }


def reset_all_breakers() -> None:
    """Reset all circuit breakers.

    Useful for testing or manual intervention.
    """
    for breaker in _CIRCUIT_BREAKERS.values():
        breaker.close()


# Import asyncio at the end to avoid circular import
import asyncio
