"""
Episodic Memory: API Routes
===========================

FastAPI application for the Episodic Memory service.
Exposes endpoints for storing, retrieving, and managing memories.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.memory_store import MemoryStore
from core.context_builder import ContextBuilder
from models.memory import Memory, MemoryQuery, MemorySearchResult, MemoryType


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Initialize FastAPI app
app = FastAPI(
    title="Episodic Memory Service",
    description="Service for long-term agent memory storage and retrieval",
    version="1.0.0"
)


# Global state
store: MemoryStore = MemoryStore()


class StoreMemoryRequest(BaseModel):
    """Request to store a memory"""
    content: str
    type: MemoryType
    context: Optional[Dict[str, Any]] = None


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Service health check.

    Returns:
        Status dictionary.
    """
    return {
        "status": "healthy",
        "service": "episodic_memory",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/v1/memories", response_model=Memory)
async def store_memory(request: StoreMemoryRequest) -> Memory:
    """
    Store a new memory.

    Args:
        request: Memory details

    Returns:
        Created memory object
    """
    try:
        memory = await store.store(request.content, request.type, request.context)
        return memory
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Failed to store memory: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/v1/memories/search", response_model=MemorySearchResult)
async def search_memories(query: MemoryQuery) -> MemorySearchResult:
    """
    Search for memories.

    Args:
        query: Search criteria

    Returns:
        Search results
    """
    try:
        results = await store.retrieve(query)
        return results
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Search failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/v1/memories/stats")
async def get_stats() -> Dict[str, Any]:
    """
    Get memory store statistics.

    Returns:
        Total count, counts by type, average importance
    """
    try:
        stats = await store.get_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        logger.error("Stats retrieval failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/v1/memories/{memory_id}", response_model=Memory)
async def get_memory(
    memory_id: str = Path(..., description="ID of the memory to retrieve")
) -> Memory:
    """
    Get a specific memory by ID.

    Args:
        memory_id: ID to look up

    Returns:
        Memory object
    """
    memory = await store.get_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory


@app.delete("/v1/memories/{memory_id}")
async def delete_memory(
    memory_id: str = Path(..., description="ID of the memory to delete")
) -> Dict[str, bool]:
    """
    Delete a memory.

    Args:
        memory_id: ID to delete

    Returns:
        Success status
    """
    success = await store.delete(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"success": True}


class ConsolidateRequest(BaseModel):
    """Request to consolidate memories to vault."""
    threshold: float = 0.8
    min_age_days: int = 7
    min_access_count: int = 2


class DecayRequest(BaseModel):
    """Request to apply importance decay."""
    decay_factor: float = 0.995
    boost_recent_access: bool = True
    delete_threshold: float = 0.05


class ContextRequest(BaseModel):
    """Request for task context."""
    task: str


@app.post("/v1/memories/consolidate")
async def consolidate_memories(request: ConsolidateRequest) -> Dict[str, Any]:
    """
    Consolidate high-importance memories to vault.

    Moves memories that meet criteria to VAULT type for long-term storage.

    Args:
        request: Consolidation parameters

    Returns:
        Count of consolidated memories by original type
    """
    try:
        result = await store.consolidate_to_vault(
            threshold=request.threshold,
            min_age_days=request.min_age_days,
            min_access_count=request.min_access_count
        )
        return {"success": True, "consolidated": result}
    except Exception as e:
        logger.error("Consolidation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/v1/memories/decay")
async def apply_decay(request: DecayRequest) -> Dict[str, Any]:
    """
    Apply Ebbinghaus decay to importance scores.

    Reduces importance of old memories exponentially.
    Optionally boosts recently accessed memories.
    Deletes memories below threshold.

    Args:
        request: Decay parameters

    Returns:
        Statistics: decayed, boosted, deleted counts
    """
    try:
        result = await store.decay_importance(
            decay_factor=request.decay_factor,
            boost_recent_access=request.boost_recent_access,
            delete_threshold=request.delete_threshold
        )
        return {"success": True, "stats": result}
    except Exception as e:
        logger.error("Decay failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/v1/memories/context")
async def get_task_context(request: ContextRequest) -> Dict[str, Any]:
    """
    Get multi-type memory context for a task.

    Retrieves relevant memories from all 6 MIRIX types.

    Args:
        request: Task description

    Returns:
        MemoryContext with memories organized by type
    """
    try:
        builder = ContextBuilder(store)
        context = await builder.get_context_for_task(request.task)
        return context.to_dict()
    except Exception as e:
        logger.error("Context retrieval failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.exception_handler(Exception)
async def global_exception_handler(_: Any, exc: Exception) -> JSONResponse:
    """Global exception handler."""
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8102)
