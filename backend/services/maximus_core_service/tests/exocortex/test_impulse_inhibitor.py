"""
Unit Tests for Impulse Inhibitor
================================
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from services.maximus_core_service.src.consciousness.exocortex.impulse_inhibitor import (
    ImpulseInhibitor,
    ImpulseContext,
    InterventionLevel
)
from services.maximus_core_service.utils.gemini_client import GeminiClient

class TestImpulseInhibitor:

    @pytest.fixture
    def mock_gemini(self):
        mock = MagicMock(spec=GeminiClient)
        mock.generate_text = AsyncMock()
        return mock

    @pytest.fixture
    def inhibitor(self, mock_gemini):
        return ImpulseInhibitor(gemini_client=mock_gemini)

    @pytest.mark.asyncio
    async def test_detect_rage_reply(self, inhibitor, mock_gemini):
        """Test detection of high-emotion rage reply."""
        mock_gemini.generate_text.return_value = {
            "text": '{"emotional_intensity": 0.9, "irreversibility": 0.8, "alignment": 0.2, "detected_impulse": "RAGE_REPLY", "reasoning": "Angry tone"}'
        }
        
        ctx = ImpulseContext(
            action_type="send_email",
            content="I hate you!",
            user_state="ANGRY",
            platform="email"
        )
        
        intervention = await inhibitor.check_impulse(ctx)
        
        assert intervention.level == InterventionLevel.PAUSE
        assert "High emotional intensity" in intervention.reasoning
        assert intervention.wait_time_seconds == 30

    @pytest.mark.asyncio
    async def test_safe_action(self, inhibitor, mock_gemini):
        """Test allowing a safe action."""
        mock_gemini.generate_text.return_value = {
            "text": '{"emotional_intensity": 0.1, "irreversibility": 0.1, "alignment": 1.0, "detected_impulse": "NONE", "reasoning": "Calm"}'
        }
        
        ctx = ImpulseContext(
            action_type="write_doc",
            content="Hello world",
            user_state="CALM",
            platform="docs"
        )
        
        intervention = await inhibitor.check_impulse(ctx)
        
        assert intervention.level == InterventionLevel.NONE

    @pytest.mark.asyncio
    async def test_fallback_on_error(self, inhibitor, mock_gemini):
        """Test fail-safe behavior on API error."""
        mock_gemini.generate_text.side_effect = Exception("API Down")
        
        ctx = ImpulseContext(action_type="unknown", content="", user_state="unknown", platform="unknown")
        intervention = await inhibitor.check_impulse(ctx)
        
        # Should fail safe (NONE)
        assert intervention.level == InterventionLevel.NONE
