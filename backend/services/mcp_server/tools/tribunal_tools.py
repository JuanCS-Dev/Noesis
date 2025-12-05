"""
Tribunal MCP Tools
==================

MCP tools for Tribunal (metacognitive_reflector) service.

Follows CODE_CONSTITUTION: Clarity Over Cleverness, Safety First.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

# Note: FastMCP will be imported in main.py to avoid circular dependencies
# Tools are registered via decorator at runtime


class TribunalEvaluateRequest(BaseModel):
    """Request model for tribunal evaluation.

    Attributes:
        execution_log: Execution log to evaluate (max 10k chars)
        context: Additional context (optional)
    """

    execution_log: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Execution log to evaluate"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context for evaluation"
    )


class TribunalEvaluateResponse(BaseModel):
    """Response model for tribunal evaluation.

    Attributes:
        decision: Tribunal decision (PASS, REVIEW, FAIL, CAPITAL)
        consensus_score: Weighted consensus score (0.0-1.0)
        verdicts: Individual judge verdicts
        punishment: Punishment if applicable (optional)
        trace_id: Request trace ID for debugging
    """

    decision: str = Field(
        ...,
        pattern="^(PASS|REVIEW|FAIL|CAPITAL)$",
        description="Tribunal decision"
    )
    consensus_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Weighted consensus score"
    )
    verdicts: Dict[str, Any] = Field(
        ...,
        description="Individual judge verdicts"
    )
    punishment: Optional[str] = Field(
        default=None,
        description="Punishment if applicable"
    )
    trace_id: str = Field(
        ...,
        description="Request trace ID"
    )


async def tribunal_evaluate(
    execution_log: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Avalia execução no Tribunal de Juízes.

    This tool sends execution logs to the Tribunal (metacognitive_reflector)
    for evaluation by three judges:
    - VERITAS (40%): Truth verification via semantic entropy + RAG
    - SOPHIA (30%): Wisdom/depth analysis via CoT reasoning
    - DIKĒ (30%): Justice/authorization via policy checks

    The Tribunal uses weighted voting to reach consensus and may apply
    punishments (RE_EDUCATION, QUARANTINE) for failures.

    Circuit breaker protects against cascading failures if Tribunal
    becomes overloaded.

    Args:
        execution_log: Log of execution to evaluate (max 10k characters)
        context: Additional context for evaluation (optional)

    Returns:
        Tribunal verdict with decision, scores, and punishments

    Raises:
        ServiceUnavailableError: If circuit breaker is open
        RateLimitExceededError: If rate limit exceeded
        ValidationError: If input validation fails

    Example:
        >>> verdict = await tribunal_evaluate(
        ...     "task: generate_tests\\nresult: 5 tests created",
        ...     context={"service": "tool_factory"}
        ... )
        >>> verdict["decision"]
        'PASS'
        >>> verdict["consensus_score"]
        0.85
    """
    # Validation happens automatically via Pydantic
    request = TribunalEvaluateRequest(
        execution_log=execution_log,
        context=context
    )

    # Get clients from dependency injection (set by FastMCP)
    # This will be injected at runtime by main.py
    from clients.tribunal_client import TribunalClient
    from config import get_config
    from middleware.circuit_breaker import with_circuit_breaker

    config = get_config()
    client = TribunalClient(config)

    # Call with circuit breaker protection
    @with_circuit_breaker("tribunal", failure_threshold=5, timeout=30.0)
    async def call_tribunal():
        return await client.evaluate(
            request.execution_log,
            request.context
        )

    try:
        result = await call_tribunal()

        # Validate response
        response = TribunalEvaluateResponse(**result)
        return response.model_dump()

    finally:
        await client.close()


async def tribunal_health() -> Dict[str, Any]:
    """
    Retorna saúde do Tribunal.

    Checks health status of the Tribunal service including:
    - Individual judge status (VERITAS, SOPHIA, DIKĒ)
    - Circuit breaker state
    - Recent evaluation statistics

    Returns:
        Health status dict with judge statuses and metrics

    Example:
        >>> health = await tribunal_health()
        >>> health["status"]
        'healthy'
        >>> health["judges"]["VERITAS"]["status"]
        'operational'
    """
    from clients.tribunal_client import TribunalClient
    from config import get_config

    config = get_config()
    client = TribunalClient(config)

    try:
        result = await client.get_health()
        return result
    finally:
        await client.close()


async def tribunal_stats() -> Dict[str, Any]:
    """
    Retorna estatísticas do Tribunal.

    Returns:
        Statistics including:
        - Total evaluations
        - Decisions breakdown (PASS/REVIEW/FAIL/CAPITAL)
        - Average consensus scores
        - Punishment statistics

    Example:
        >>> stats = await tribunal_stats()
        >>> stats["total_evaluations"]
        1523
        >>> stats["decisions"]["PASS"]
        1245
    """
    from clients.tribunal_client import TribunalClient
    from config import get_config

    config = get_config()
    client = TribunalClient(config)

    try:
        result = await client.get_stats()
        return result
    finally:
        await client.close()
