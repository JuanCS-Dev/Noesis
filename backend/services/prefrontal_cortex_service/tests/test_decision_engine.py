"""
Unit tests for DecisionEngine.
"""

from __future__ import annotations

import pytest

from backend.services.prefrontal_cortex_service.config import CognitiveSettings
from backend.services.prefrontal_cortex_service.core.decision_engine import (
    DecisionEngine
)


@pytest.fixture(name="settings")
def fixture_settings() -> CognitiveSettings:
    """Cognitive settings fixture."""
    return CognitiveSettings(decision_timeout=10.0, max_tasks=100)


@pytest.fixture(name="engine")
def fixture_engine(settings: CognitiveSettings) -> DecisionEngine:
    """Decision engine fixture."""
    return DecisionEngine(settings)


@pytest.mark.asyncio
async def test_make_decision_with_context(engine: DecisionEngine) -> None:
    """Test making decision with context match."""
    context = {"task": "Prioritize option_a over others"}
    options = ["option_a", "option_b", "option_c"]

    decision = await engine.make_decision(context, options)

    assert decision.selected_option == "option_a"
    assert decision.confidence > 0.5
    assert decision.reasoning is not None


@pytest.mark.asyncio
async def test_make_decision_no_context(engine: DecisionEngine) -> None:
    """Test making decision without context match."""
    context = {"task": "Some unrelated task"}
    options = ["option_x", "option_y"]

    decision = await engine.make_decision(context, options)

    assert decision.selected_option in options
    assert 0.0 <= decision.confidence <= 1.0


@pytest.mark.asyncio
async def test_make_decision_no_options(engine: DecisionEngine) -> None:
    """Test making decision with no options."""
    context = {"task": "Some task"}
    options: list[str] = []

    decision = await engine.make_decision(context, options)

    assert decision.selected_option is None
    assert decision.confidence == 0.0
    assert "No options" in decision.reasoning
