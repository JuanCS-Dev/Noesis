"""
Metacognitive Reflector - API Routes
====================================

FastAPI endpoints for reflection, tribunal, and punishment management.
"""

from __future__ import annotations


from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..core.memory_client import MemoryClient
from ..core.reflector import Reflector
from ..core.judges import TribunalDecision, TribunalVerdict
from ..models.reflection import (
    Critique,
    ExecutionLog,
    MemoryUpdate,
    ReflectionResponse,
)
from .dependencies import get_memory_client, get_reflector

router = APIRouter()


# =============================================================================
# Response Models
# =============================================================================


class VerdictResponse(BaseModel):
    """Response with full tribunal verdict details."""

    critique: Critique
    verdict: Dict[str, Any] = Field(..., description="Full tribunal verdict")
    memory_updates: List[MemoryUpdate]
    punishment_action: Optional[str] = None


class AgentStatusResponse(BaseModel):
    """Response for agent punishment status."""

    agent_id: str
    active: bool = Field(..., description="Whether punishment is active")
    status: str = Field(..., description="Current status")
    punishment_type: Optional[str] = None
    started_at: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class PardonRequest(BaseModel):
    """Request to pardon an agent."""

    reason: str = Field(..., min_length=1, description="Reason for pardon")


class PardonResponse(BaseModel):
    """Response for pardon request."""

    success: bool
    agent_id: str
    message: str


class TribunalHealthResponse(BaseModel):
    """Detailed tribunal health response."""

    healthy: bool
    tribunal: Dict[str, Any]
    executor: Dict[str, Any]
    memory: Dict[str, Any]


class ServiceHealthResponse(BaseModel):
    """Simple service health response."""

    status: str
    service: str


# =============================================================================
# Health Endpoints
# =============================================================================


@router.get("/health", response_model=ServiceHealthResponse)
async def health_check() -> ServiceHealthResponse:
    """
    Service health check.

    Returns basic service health status.
    """
    return ServiceHealthResponse(
        status="healthy",
        service="metacognitive-reflector"
    )


@router.get("/health/detailed", response_model=TribunalHealthResponse)
async def detailed_health_check(
    reflector: Reflector = Depends(get_reflector),
) -> TribunalHealthResponse:
    """
    Detailed tribunal health check.

    Returns health status of all tribunal components:
    - Tribunal (judges)
    - Punishment executor
    - Memory client
    """
    health = await reflector.health_check()
    return TribunalHealthResponse(
        healthy=health.get("healthy", False),
        tribunal=health.get("tribunal", {}),
        executor=health.get("executor", {}),
        memory=health.get("memory", {}),
    )


# =============================================================================
# Reflection Endpoints
# =============================================================================


@router.post("/reflect", response_model=ReflectionResponse)
async def reflect_on_execution(
    log: ExecutionLog,
    reflector: Reflector = Depends(get_reflector),
    memory_client: MemoryClient = Depends(get_memory_client),
) -> ReflectionResponse:
    """
    Analyze an execution log and provide a critique.

    This endpoint:
    1. Analyzes the log using the Three Judges tribunal.
    2. Determines offense level and punishment.
    3. Generates memory updates.
    4. Applies updates to shared memory.

    Args:
        log: Execution log to analyze

    Returns:
        ReflectionResponse with critique, updates, and punishment
    """
    # 1. Analyze using tribunal
    critique = await reflector.analyze_log(log)

    # 2. Generate memory updates
    memory_updates = await reflector.generate_memory_updates(critique)

    # 3. Determine punishment action
    punishment = await reflector.apply_punishment(critique.offense_level)

    # 4. Apply memory updates
    if memory_updates:
        await memory_client.apply_updates(memory_updates)

    return ReflectionResponse(
        critique=critique,
        memory_updates=memory_updates,
        punishment_action=punishment,
    )


@router.post("/reflect/verdict", response_model=VerdictResponse)
async def reflect_with_verdict(
    log: ExecutionLog,
    reflector: Reflector = Depends(get_reflector),
    memory_client: MemoryClient = Depends(get_memory_client),
) -> VerdictResponse:
    """
    Analyze execution log with full tribunal verdict details.

    Returns comprehensive verdict including:
    - Individual judge verdicts
    - Vote breakdown
    - Consensus score
    - Punishment recommendation

    Args:
        log: Execution log to analyze

    Returns:
        VerdictResponse with critique, full verdict, and updates
    """
    # Get critique and raw verdict
    critique, verdict = await reflector.analyze_with_verdict(log)

    # Generate memory updates
    memory_updates = await reflector.generate_memory_updates(critique)

    # Convert verdict to dict for response
    verdict_dict = {
        "decision": verdict.decision.value,
        "consensus_score": verdict.consensus_score,
        "individual_verdicts": {
            name: {
                "pillar": v.pillar,
                "passed": v.passed,
                "confidence": v.confidence,
                "reasoning": v.reasoning,
                "suggestions": v.suggestions,
            }
            for name, v in verdict.individual_verdicts.items()
        },
        "vote_breakdown": [
            {
                "judge_name": v.judge_name,
                "pillar": v.pillar,
                "vote": v.vote,
                "weight": v.weight,
                "weighted_vote": v.weighted_vote,
                "abstained": v.abstained,
            }
            for v in verdict.vote_breakdown
        ],
        "reasoning": verdict.reasoning,
        "offense_level": verdict.offense_level,
        "requires_human_review": verdict.requires_human_review,
        "punishment_recommendation": verdict.punishment_recommendation,
        "abstention_count": verdict.abstention_count,
        "execution_time_ms": verdict.execution_time_ms,
    }

    # Apply memory updates
    if memory_updates:
        await memory_client.apply_updates(memory_updates)

    return VerdictResponse(
        critique=critique,
        verdict=verdict_dict,
        memory_updates=memory_updates,
        punishment_action=verdict.punishment_recommendation,
    )


# =============================================================================
# Agent Management Endpoints
# =============================================================================


@router.get("/agent/{agent_id}/status", response_model=AgentStatusResponse)
async def get_agent_status(
    agent_id: str,
    reflector: Reflector = Depends(get_reflector),
) -> AgentStatusResponse:
    """
    Get punishment status for an agent.

    Returns current punishment status including:
    - Whether punishment is active
    - Punishment type
    - When it started

    Args:
        agent_id: Agent identifier

    Returns:
        AgentStatusResponse with status details
    """
    status_data = await reflector.check_agent_status(agent_id)

    return AgentStatusResponse(
        agent_id=agent_id,
        active=status_data.get("active", False),
        status=status_data.get("status", "unknown"),
        punishment_type=status_data.get("punishment_type"),
        started_at=status_data.get("started_at"),
        details=status_data,
    )


@router.post("/agent/{agent_id}/pardon", response_model=PardonResponse)
async def pardon_agent(
    agent_id: str,
    request: PardonRequest,
    reflector: Reflector = Depends(get_reflector),
) -> PardonResponse:
    """
    Pardon an agent (clear active punishment).

    Requires a reason for the pardon which will be logged.

    Args:
        agent_id: Agent to pardon
        request: Pardon request with reason

    Returns:
        PardonResponse with success status
    """
    success = await reflector.pardon_agent(agent_id, request.reason)

    if success:
        return PardonResponse(
            success=True,
            agent_id=agent_id,
            message=f"Agent {agent_id} has been pardoned. Reason: {request.reason}",
        )

    return PardonResponse(
        success=False,
        agent_id=agent_id,
        message=f"No active punishment found for agent {agent_id}",
    )


@router.post(
    "/agent/{agent_id}/execute-punishment",
    response_model=Dict[str, Any],
)
async def execute_agent_punishment(
    agent_id: str,
    log: ExecutionLog,
    reflector: Reflector = Depends(get_reflector),
) -> Dict[str, Any]:
    """
    Analyze and execute punishment for an agent.

    This endpoint:
    1. Analyzes the execution log
    2. Determines offense level
    3. Executes appropriate punishment

    Args:
        agent_id: Agent to potentially punish
        log: Execution log that triggered the analysis

    Returns:
        Punishment outcome details
    """
    # Analyze the log
    critique = await reflector.analyze_log(log)

    # Execute punishment if warranted
    outcome = await reflector.execute_punishment(
        agent_id=agent_id,
        offense_level=critique.offense_level,
        context={"trace_id": log.trace_id, "task": log.task},
    )

    if outcome is None:
        return {
            "agent_id": agent_id,
            "punishment_executed": False,
            "reason": "No offense detected",
            "offense_level": critique.offense_level.value,
        }

    return {
        "agent_id": agent_id,
        "punishment_executed": True,
        "result": outcome.result.value,
        "handler": outcome.handler,
        "actions_taken": outcome.actions_taken,
        "message": outcome.message,
        "requires_followup": outcome.requires_followup,
    }
