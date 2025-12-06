"""
MAXIMUS 2.0 - Resilience Patterns for the Tribunal
===================================================

Implements:
1. Circuit Breaker - Fail fast when judge is unhealthy
2. Timeout Wrapper - Individual timeouts per judge
3. Abstention Handling - Graceful degradation

Based on:
- Netflix Hystrix patterns
- Microsoft resilience patterns
- Cloud-native circuit breaker design

Architecture:
    ┌─────────────────────────────────────────────────────────┐
    │           RESILIENT TRIBUNAL PATTERN                     │
    ├─────────────────────────────────────────────────────────┤
    │  ┌─────────┐  ┌─────────┐  ┌─────────┐                  │
    │  │ VERITAS │  │ SOPHIA  │  │  DIKĒ   │                  │
    │  │ timeout │  │ timeout │  │ timeout │                  │
    │  │   3s    │  │   10s   │  │   3s    │                  │
    │  │ circuit │  │ circuit │  │ circuit │                  │
    │  │ breaker │  │ breaker │  │ breaker │                  │
    │  └────┬────┘  └────┬────┘  └────┬────┘                  │
    │       │            │            │                        │
    │       └────────────┴────────────┘                        │
    │                    │                                     │
    │  On Timeout/Error: ABSTAIN vote (confidence=0.0)        │
    │                                                          │
    │  Circuit Breaker States:                                │
    │  • CLOSED: Normal operation                             │
    │  • OPEN: Judge failing → skip to ABSTAIN immediately    │
    │  • HALF-OPEN: Test with single request after cooldown   │
    └─────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from .base import Evidence, JudgePlugin, JudgeVerdict, VerdictType


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing, skip calls
    HALF_OPEN = "half_open" # Testing recovery


@dataclass
class CircuitBreaker:
    """
    Circuit breaker for judge calls.

    Implements the circuit breaker pattern to prevent cascade failures:
    - CLOSED: Normal operation, requests flow through
    - OPEN: After failure_threshold failures, requests fail immediately
    - HALF_OPEN: After recovery_timeout, allow one test request

    Usage:
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0)

        if breaker.is_open():
            return abstain_verdict()

        try:
            result = await judge.evaluate(...)
            breaker.record_success()
            return result
        except Exception:
            breaker.record_failure()
            return abstain_verdict()
    """

    failure_threshold: int = 3
    recovery_timeout: float = 60.0  # seconds
    success_threshold: int = 2  # Successes needed to close from half-open

    _failures: int = field(default=0, init=False)
    _successes: int = field(default=0, init=False)
    _last_failure: Optional[datetime] = field(default=None, init=False)
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)

    @property
    def state(self) -> CircuitState:
        """Get current state, transitioning if needed."""
        if self._state == CircuitState.OPEN:
            if self._last_failure and \
               (datetime.now() - self._last_failure).total_seconds() > self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._successes = 0
        return self._state

    def record_success(self) -> None:
        """Record a successful call."""
        if self._state == CircuitState.HALF_OPEN:
            self._successes += 1
            if self._successes >= self.success_threshold:
                self._state = CircuitState.CLOSED
                self._failures = 0
        elif self._state == CircuitState.CLOSED:
            self._failures = max(0, self._failures - 1)  # Decay failures

    def record_failure(self) -> None:
        """Record a failed call."""
        self._failures += 1
        self._last_failure = datetime.now()

        if self._state == CircuitState.HALF_OPEN:
            # Any failure in half-open immediately opens
            self._state = CircuitState.OPEN
        elif self._failures >= self.failure_threshold:
            self._state = CircuitState.OPEN

    def is_open(self) -> bool:
        """Check if circuit is open (calls should fail fast)."""
        return self.state == CircuitState.OPEN

    def is_half_open(self) -> bool:
        """Check if circuit is in testing state."""
        return self.state == CircuitState.HALF_OPEN

    def reset(self) -> None:
        """Reset circuit to closed state."""
        self._failures = 0
        self._successes = 0
        self._last_failure = None
        self._state = CircuitState.CLOSED

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit statistics."""
        return {
            "state": self.state.value,
            "failures": self._failures,
            "successes": self._successes,
            "last_failure": self._last_failure.isoformat() if self._last_failure else None,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
        }


class ResilientJudgeWrapper:  # pylint: disable=too-many-instance-attributes
    """
    Wraps a judge with timeout and circuit breaker.

    Provides resilience features:
    1. Per-judge timeout (VERITAS=3s, SOPHIA=10s, DIKĒ=3s)
    2. Circuit breaker to prevent cascade failures
    3. Abstention handling for graceful degradation

    Usage:
        wrapper = ResilientJudgeWrapper(veritas_judge)
        verdict = await wrapper.evaluate(execution_log)
        # Returns abstained verdict on timeout/error
    """

    # Default timeouts per judge type
    DEFAULT_TIMEOUTS: Dict[str, float] = {
        "VERITAS": 3.0,   # Fast (uses cache)
        "SOPHIA": 10.0,   # Slow (memory queries)
        "DIKĒ": 3.0,      # Fast (rule-based)
    }

    def __init__(
        self,
        judge: JudgePlugin,
        timeout: Optional[float] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ):
        """
        Initialize wrapper.

        Args:
            judge: The judge to wrap
            timeout: Custom timeout (uses default if None)
            circuit_breaker: Custom circuit breaker
        """
        self._judge = judge
        self._timeout = timeout or self.DEFAULT_TIMEOUTS.get(
            judge.name, judge.timeout_seconds
        )
        self._circuit = circuit_breaker or CircuitBreaker()

        # Statistics
        self._call_count = 0
        self._success_count = 0
        self._timeout_count = 0
        self._error_count = 0
        self._abstention_count = 0

    @property
    def name(self) -> str:
        """Judge name."""
        return self._judge.name

    @property
    def pillar(self) -> str:
        """Judge pillar."""
        return self._judge.pillar

    @property
    def weight(self) -> float:
        """Judge weight."""
        return self._judge.weight

    @property
    def timeout(self) -> float:
        """Configured timeout."""
        return self._timeout

    @property
    def circuit_state(self) -> CircuitState:
        """Current circuit breaker state."""
        return self._circuit.state

    async def evaluate(
        self,
        execution_log: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> JudgeVerdict:
        """
        Evaluate with timeout and circuit breaker.

        Returns abstained verdict on:
        - Circuit breaker open
        - Timeout
        - Any exception
        """
        self._call_count += 1
        start_time = time.time()

        # Check circuit breaker first
        if self._circuit.is_open():
            self._abstention_count += 1
            return self._abstain_verdict(
                "Circuit breaker open - judge is unhealthy",
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        try:
            # Execute with timeout
            verdict = await asyncio.wait_for(
                self._judge.evaluate(execution_log, context),
                timeout=self._timeout
            )

            # Record success
            self._circuit.record_success()
            self._success_count += 1

            return verdict

        except asyncio.TimeoutError:
            self._circuit.record_failure()
            self._timeout_count += 1
            return self._abstain_verdict(
                f"Timeout after {self._timeout}s",
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        except (ValueError, KeyError, TypeError, RuntimeError) as e:
            self._circuit.record_failure()
            self._error_count += 1
            return self._abstain_verdict(
                f"Error: {str(e)[:100]}",
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    def _abstain_verdict(
        self,
        reason: str,
        execution_time_ms: float = 0.0,
    ) -> JudgeVerdict:
        """Create abstention verdict."""
        return JudgeVerdict(
            judge_name=self._judge.name,
            pillar=self._judge.pillar,
            verdict=VerdictType.ABSTAIN,
            passed=False,
            confidence=0.0,
            reasoning=f"ABSTAINED: {reason}",
            evidence=[
                Evidence(
                    source="circuit_breaker",
                    content=reason,
                    relevance=1.0,
                    verified=True,
                )
            ],
            suggestions=[],
            execution_time_ms=execution_time_ms,
            metadata={
                "abstained": True,
                "reason": reason,
                "circuit_state": self._circuit.state.value,
            }
        )

    async def health_check(self) -> Dict[str, Any]:
        """Get wrapper health status."""
        judge_health = await self._judge.health_check()
        circuit_stats = self._circuit.get_stats()

        return {
            "healthy": not self._circuit.is_open() and judge_health.get("healthy", True),
            "judge": judge_health,
            "circuit": circuit_stats,
            "timeout": self._timeout,
            "stats": {
                "total_calls": self._call_count,
                "successes": self._success_count,
                "timeouts": self._timeout_count,
                "errors": self._error_count,
                "abstentions": self._abstention_count,
                "success_rate": (
                    self._success_count / self._call_count
                    if self._call_count > 0 else 1.0
                ),
            },
        }

    def reset_circuit(self) -> None:
        """Reset circuit breaker."""
        self._circuit.reset()

    def get_stats(self) -> Dict[str, Any]:
        """Get wrapper statistics."""
        return {
            "name": self.name,
            "pillar": self.pillar,
            "timeout": self._timeout,
            "circuit_state": self._circuit.state.value,
            "calls": self._call_count,
            "successes": self._success_count,
            "timeouts": self._timeout_count,
            "errors": self._error_count,
            "abstentions": self._abstention_count,
        }
