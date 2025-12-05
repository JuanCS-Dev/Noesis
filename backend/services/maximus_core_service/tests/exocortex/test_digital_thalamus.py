"""
Unit Tests for Digital Thalamus
===============================
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from services.maximus_core_service.src.consciousness.exocortex.digital_thalamus import (
    DigitalThalamus,
    Stimulus,
    StimulusType,
    AttentionStatus
)
from services.maximus_core_service.utils.gemini_client import GeminiClient

class TestDigitalThalamus:
    
    @pytest.fixture
    def mock_gemini(self):
        mock = MagicMock(spec=GeminiClient)
        mock.generate_text = AsyncMock()
        return mock

    @pytest.fixture
    def thalamus(self, mock_gemini):
        return DigitalThalamus(gemini_client=mock_gemini)

    @pytest.mark.asyncio
    async def test_hard_block_ads_in_focus(self, thalamus):
        """Test circuit breaker: Block ads in FOCUS mode."""
        stim = Stimulus(
            id="1", type=StimulusType.ADVERTISEMENT, source="AdNet", content="Buy this!"
        )
        decision = await thalamus.filter_stimulus(stim, AttentionStatus.FOCUS)
        
        assert decision.action == "BLOCK"
        assert "Absolute block" in decision.reasoning
        # Should NOT call LLM
        thalamus.client.generate_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_allow_high_relevance_in_focus(self, thalamus, mock_gemini):
        """Test allowing critical alerts even in FOCUS."""
        mock_gemini.generate_text.return_value = {
            "text": '{"urgency": 0.9, "dopamine": 0.1, "relevance": 1.0, "brief_reasoning": "Server Down"}'
        }
        
        stim = Stimulus(
            id="2", type=StimulusType.SYSTEM_ALERT, source="PagerDuty", content="Prod Down"
        )
        decision = await thalamus.filter_stimulus(stim, AttentionStatus.FOCUS)
        
        assert decision.action == "ALLOW"
        assert decision.urgency_score == 0.9

    @pytest.mark.asyncio
    async def test_batch_low_urgency_in_flow(self, thalamus, mock_gemini):
        """Test batching non-urgent items in FLOW."""
        mock_gemini.generate_text.return_value = {
            "text": '{"urgency": 0.3, "dopamine": 0.5, "relevance": 0.2, "brief_reasoning": "Meme"}'
        }
        
        stim = Stimulus(
            id="3", type=StimulusType.MESSAGE, source="Friend", content="Look at this cat"
        )
        decision = await thalamus.filter_stimulus(stim, AttentionStatus.FLOW)
        
        assert decision.action == "BATCH"
        assert "Flow protection" in decision.reasoning

    @pytest.mark.asyncio
    async def test_fallback_on_gemini_failure(self, thalamus, mock_gemini):
        """Test safe fallback if LLM crashes."""
        mock_gemini.generate_text.side_effect = Exception("API Error")
        
        stim = Stimulus(
            id="4", type=StimulusType.NOTIFICATION, source="App", content="Ping"
        )
        
        # Should not crash
        decision = await thalamus.filter_stimulus(stim, AttentionStatus.NEUTRAL)
        
        assert decision.action == "ALLOW" # Default is allow but logged
        assert "Analysis Failed" in decision.reasoning
