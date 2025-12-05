"""
Consciousness Test Configuration.

Fixes event loop issues when running full test suite.
The api.py has startup events with background tasks that can cause hangs.
"""
from __future__ import annotations

import asyncio
import gc
import pytest


@pytest.fixture(scope="function")
def event_loop():
    """Create a new event loop for each test function.

    This prevents event loop pollution between tests, especially important
    when TestClient triggers FastAPI startup/shutdown events with background tasks.
    """
    loop = asyncio.new_event_loop()
    yield loop
    # Clean up any pending tasks
    pending = asyncio.all_tasks(loop)
    for task in pending:
        task.cancel()
    # Give tasks a chance to handle cancellation
    if pending:
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    loop.close()
    
    # Aggressive cleanup
    gc.collect()
    
@pytest.fixture(autouse=True)
def aggressive_gc():
    """Force garbage collection before and after each test."""
    gc.collect()
    yield
    gc.collect()
