"""
Test Suite for Gemini Client v3.0
=================================

Tests thinking budget, temporal grounding, and JSON schema output.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Generator, Any, Dict

from services.maximus_core_service.utils.gemini_client import (
    GeminiClient,
    GeminiConfig
)

class TestGeminiClient:
    """Test suite for GeminiClient."""

    @pytest.fixture
    def mock_config(self) -> GeminiConfig:
        """Fixture for Gemini configuration."""
        return GeminiConfig(
            api_key="fake_key",
            thinking_level="HIGH"
        )

    @pytest.fixture
    def client(self, mock_config: GeminiConfig) -> GeminiClient:
        """Fixture for GeminiClient instance."""
        return GeminiClient(config=mock_config)

    def test_initialization(self, client: GeminiClient) -> None:
        """Test client initialization."""
        assert client.api_key == "fake_key"
        assert client.config.thinking_level == "HIGH"
        assert client.model == "gemini-3.0-pro-001"

    def test_temporal_context(self, client: GeminiClient) -> None:
        """Test temporal grounding injection."""
        context = client._get_temporal_context()
        assert "SYSTEM OVERRIDE" in context
        assert datetime.now().strftime("%Y") in context
        assert "Gemini 3.0" in context

    @pytest.mark.asyncio
    async def test_generate_text_with_thinking(self, client: GeminiClient) -> None:
        """Test generation with thinking config."""
        mock_response = {
            "candidates": [{
                "content": {"parts": [{"text": "Result"}]},
                "finishReason": "STOP"
            }]
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            # Mocking response object explicitly to avoid coroutine issues with .json()
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_post.return_value = mock_response_obj

            result = await client.generate_text("Test prompt")

            # Verify request structure
            call_kwargs = mock_post.call_args[1]
            json_body = call_kwargs["json"]
            
            # Check Thinking Config
            assert "thinkingConfig" in json_body["generationConfig"]
            assert json_body["generationConfig"]["thinkingConfig"]["includeThoughts"] is True
            
            # Check Temporal Grounding
            system_instr = json_body["systemInstruction"]["parts"][0]["text"]
            assert "SYSTEM OVERRIDE" in system_instr

            assert result["text"] == "Result"

    @pytest.mark.asyncio
    async def test_generate_with_schema(self, client: GeminiClient) -> None:
        """Test generation with JSON schema."""
        schema = {"type": "object", "properties": {"foo": {"type": "string"}}}
        
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = {"candidates": []}
            mock_post.return_value = mock_response_obj

            await client.generate_text("Test", response_schema=schema)
            
            json_body = mock_post.call_args[1]["json"]
            assert json_body["generationConfig"]["responseMimeType"] == "application/json"
            assert json_body["generationConfig"]["responseSchema"] == schema

    @pytest.mark.asyncio
    async def test_generate_text_api_error(self, client: GeminiClient) -> None:
        """Test generation handling API error."""
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 500
            mock_response_obj.text = "Internal Server Error"
            mock_post.return_value = mock_response_obj

            with pytest.raises(Exception, match="Gemini Error: 500"):
                await client.generate_text("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_embeddings_success(self, client: GeminiClient) -> None:
        """Test successful embeddings generation."""
        mock_response = {
            "embedding": {"values": [0.1, 0.2, 0.3]}
        }
        
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_post.return_value = mock_response_obj

            result = await client.generate_embeddings("Test text")
            assert result == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_generate_embeddings_error(self, client: GeminiClient) -> None:
        """Test embeddings generation error."""
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 403
            mock_post.return_value = mock_response_obj

            with pytest.raises(Exception, match="Embeddings Error: 403"):
                await client.generate_embeddings("Test text")

    def test_convert_tools(self, client: GeminiClient) -> None:
        """Test tool conversion format."""
        tools = [
            {
                "name": "my_tool",
                "description": "Does something",
                "parameters": {"type": "object"}
            }
        ]
        converted = client._convert_tools(tools)
        assert len(converted) == 1
        assert converted[0]["name"] == "my_tool"
        assert converted[0]["parameters"]["type"] == "object"