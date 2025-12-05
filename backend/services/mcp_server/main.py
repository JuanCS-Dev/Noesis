"""
MAXIMUS MCP Server
==================

FastAPI + MCP dual protocol server following elite patterns.

Provides both REST API and Model Context Protocol access to MAXIMUS services:
- Tribunal (metacognitive_reflector) evaluation
- Tool Factory (tool_factory_service) generation
- Episodic Memory (episodic_memory) storage/retrieval

Based on: FastMCP 2.0 (December 2025 patterns)

Follows CODE_CONSTITUTION: All pillars.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from config import get_config
from middleware.structured_logger import LoggingMiddleware, StructuredLogger

# Initialize config and logger
config = get_config()
logger = StructuredLogger(config.service_name, config.log_level)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager.

    Initializes resources on startup, cleans up on shutdown.
    """
    logger.info(
        "Starting MAXIMUS MCP Server",
        version="2.0.0",
        mcp_timeout=config.mcp_request_timeout,
    )

    # Mount MCP endpoint on startup
    mcp = get_mcp_server()
    if mcp is not None:
        try:
            mcp_http_app = mcp.http_app(stateless_http=config.mcp_stateless_http)
            fastapi_app.mount("/mcp", mcp_http_app)
            logger.info("MCP endpoint mounted at /mcp")
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning("Failed to mount MCP endpoint: %s", str(e))

    yield

    logger.info("Shutting down MAXIMUS MCP Server")


# Create FastAPI application
app = FastAPI(
    title="MAXIMUS MCP Server",
    description="Model Context Protocol server for MAXIMUS 2.0",
    version="2.0.0",
    lifespan=lifespan,
)

# Add logging middleware
app.add_middleware(LoggingMiddleware, logger=logger)


# === REST API Endpoints (Traditional HTTP) ===
# Note: Imports inside functions are intentional for lazy loading
# pylint: disable=import-outside-toplevel


@app.get("/health")
async def health() -> Dict[str, Any]:
    """Health check for load balancers.

    Returns:
        Health status dict with version and service name
    """
    return {"status": "ok", "version": "2.0.0", "service": config.service_name}


@app.get("/metrics")
async def metrics() -> Dict[str, Any]:
    """Get service metrics.

    Returns:
        Metrics dict with circuit breaker stats
    """
    from middleware.circuit_breaker import get_breaker_stats

    return {"circuit_breakers": get_breaker_stats()}


# === MCP Tool Wrappers (REST endpoints for MCP tools) ===
# These provide REST access to the same functionality exposed via MCP


@app.post("/v1/tools/tribunal/evaluate")
async def rest_tribunal_evaluate(
    execution_log: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """REST wrapper for tribunal_evaluate MCP tool.

    Args:
        execution_log: Execution log to evaluate
        context: Additional context (optional)

    Returns:
        Tribunal verdict
    """
    from tools.tribunal_tools import tribunal_evaluate

    return await tribunal_evaluate(execution_log, context)


@app.get("/v1/tools/tribunal/health")
async def rest_tribunal_health() -> Dict[str, Any]:
    """REST wrapper for tribunal_health MCP tool."""
    from tools.tribunal_tools import tribunal_health

    return await tribunal_health()


@app.get("/v1/tools/tribunal/stats")
async def rest_tribunal_stats() -> Dict[str, Any]:
    """REST wrapper for tribunal_stats MCP tool."""
    from tools.tribunal_tools import tribunal_stats

    return await tribunal_stats()


@app.post("/v1/tools/memory/store")
async def rest_memory_store(
    content: str,
    memory_type: str,
    importance: float = 0.5,
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """REST wrapper for memory_store MCP tool."""
    from tools.memory_tools import memory_store

    return await memory_store(content, memory_type, importance, tags)


@app.post("/v1/tools/memory/search")
async def rest_memory_search(
    query: str,
    memory_type: Optional[str] = None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """REST wrapper for memory_search MCP tool."""
    from tools.memory_tools import memory_search

    return await memory_search(query, memory_type, limit)


@app.post("/v1/tools/memory/consolidate")
async def rest_memory_consolidate(threshold: float = 0.8) -> Dict[str, int]:
    """REST wrapper for memory_consolidate MCP tool."""
    from tools.memory_tools import memory_consolidate

    return await memory_consolidate(threshold)


@app.post("/v1/tools/memory/context")
async def rest_memory_context(task: str) -> Dict[str, Any]:
    """REST wrapper for memory_context MCP tool."""
    from tools.memory_tools import memory_context

    return await memory_context(task)


@app.post("/v1/tools/factory/generate")
async def rest_factory_generate(
    name: str,
    description: str,
    examples: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """REST wrapper for factory_generate MCP tool."""
    from tools.factory_tools import factory_generate

    return await factory_generate(name, description, examples)


@app.post("/v1/tools/factory/execute")
async def rest_factory_execute(
    tool_name: str,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    """REST wrapper for factory_execute MCP tool."""
    from tools.factory_tools import factory_execute

    return await factory_execute(tool_name, params)


@app.get("/v1/tools/factory/list")
async def rest_factory_list() -> List[Dict[str, Any]]:
    """REST wrapper for factory_list MCP tool."""
    from tools.factory_tools import factory_list

    return await factory_list()


@app.delete("/v1/tools/factory/{tool_name}")
async def rest_factory_delete(tool_name: str) -> bool:
    """REST wrapper for factory_delete MCP tool."""
    from tools.factory_tools import factory_delete

    return await factory_delete(tool_name)


# === Error Handlers ===


@app.exception_handler(Exception)
async def global_exception_handler(request: Any, exc: Exception) -> JSONResponse:
    """Global exception handler for uncaught errors.

    Args:
        request: HTTP request
        exc: Exception raised

    Returns:
        JSON error response
    """
    logger.error(
        "Unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "type": type(exc).__name__,
        },
    )


# === MCP Server Setup ===
# FastMCP integration for Model Context Protocol
# Note: Import here to avoid issues if fastmcp is not installed


def create_mcp_server() -> Any:
    """Create and configure FastMCP server with all tools.

    Returns:
        Configured FastMCP instance or None if fastmcp not installed

    Note:
        This function is called lazily to support environments
        where fastmcp is not installed (REST-only mode).
    """
    try:
        from fastmcp import FastMCP
    except ImportError:
        logger.warning("fastmcp not installed, MCP endpoint disabled")
        return None

    # FastMCP constructor - timeout configured separately if needed
    mcp = FastMCP("maximus")

    # Import and register tools
    from tools.tribunal_tools import tribunal_evaluate, tribunal_health, tribunal_stats
    from tools.factory_tools import (
        factory_generate,
        factory_execute,
        factory_list,
        factory_delete,
    )
    from tools.memory_tools import (
        memory_store,
        memory_search,
        memory_consolidate,
        memory_context,
    )

    # Register Tribunal tools using mcp.tool() pattern
    # mcp.tool(fn) converts async function to FastMCP Tool and registers it
    mcp.tool(tribunal_evaluate)
    mcp.tool(tribunal_health)
    mcp.tool(tribunal_stats)

    # Register Factory tools
    mcp.tool(factory_generate)
    mcp.tool(factory_execute)
    mcp.tool(factory_list)
    mcp.tool(factory_delete)

    # Register Memory tools
    mcp.tool(memory_store)
    mcp.tool(memory_search)
    mcp.tool(memory_consolidate)
    mcp.tool(memory_context)

    logger.info("FastMCP server configured with 11 tools")
    return mcp


# Create MCP server (lazy initialization)
_mcp_server = None  # pylint: disable=invalid-name


def get_mcp_server() -> Any:
    """Get or create MCP server instance (singleton pattern)."""
    global _mcp_server  # pylint: disable=global-statement
    if _mcp_server is None:
        _mcp_server = create_mcp_server()
    return _mcp_server


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.service_port,
        log_level=config.log_level.lower(),
        reload=False,
    )
