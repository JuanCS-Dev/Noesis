"""
Comprehensive Tests for GeminiClient
====================================
Goal: >90% coverage for gemini_client.py
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.maximus_core_service.utils.gemini_client import (
    GeminiClient, GeminiConfig, GeminiError
)

# --- Fixtures ---
@pytest.fixture
def mock_settings():
    with patch("services.maximus_core_service.utils.gemini_client.get_settings") as mock:
        mock.return_value.llm.api_key = "test_key"
        mock.return_value.llm.model = "gemini-test"
        mock.return_value.llm.temperature = 0.5
        mock.return_value.llm.max_tokens = 100
        mock.return_value.llm.timeout = 10
        mock.return_value.llm.thinking_level = "LOW"
        yield mock

@pytest.fixture
def client(mock_settings):
    return GeminiClient()

# --- Config & Initialization Tests ---
def test_init_from_settings(mock_settings):
    client = GeminiClient()
    assert client.api_key == "test_key"
    assert client.config.thinking_level == "LOW"

def test_init_from_explicit_config():
    config = GeminiConfig(api_key="manual_key", temperature=0.9)
    client = GeminiClient(config=config)
    assert client.api_key == "manual_key"
    assert client.config.temperature == 0.9

# --- Helper Methods Tests ---
def test_temporal_context(client):
    context = client._get_temporal_context()
    assert "SYSTEM OVERRIDE" in context
    assert "Gemini 3.0 Pro" in context

def test_build_generation_config(client):
    # Default
    conf = client._build_generation_config(None, None, None)
    assert conf["temperature"] == 0.5
    assert conf["thinkingConfig"]["thinkingLevel"] == "LOW"
    
    # Override
    schema = {"type": "OBJECT"}
    conf = client._build_generation_config(0.1, 50, schema)
    assert conf["temperature"] == 0.1
    assert conf["maxOutputTokens"] == 50
    assert conf["responseMimeType"] == "application/json"

def test_convert_tools(client):
    tools = [
        {"name": "foo", "description": "bar", "input_schema": {"type": "object"}},
        {"name": "baz", "parameters": {"type": "string"}}
    ]
    converted = client._convert_tools(tools)
    assert len(converted) == 2
    assert converted[0]["name"] == "foo"
    assert converted[0]["parameters"]["type"] == "object"
    assert converted[1]["parameters"]["type"] == "string"

# --- Parsing Tests ---
def test_parse_response_empty(client):
    res = client._parse_gemini_response({})
    assert res["finish_reason"] == "error"

def test_parse_response_success(client):
    mock_api_res = {
        "candidates": [{
            "content": {"parts": [{"text": "Hello"}]},
            "finishReason": "STOP"
        }]
    }
    res = client._parse_gemini_response(mock_api_res)
    assert res["text"] == "Hello"
    assert res["finish_reason"] == "STOP"

def test_parse_response_tool_call(client):
    mock_api_res = {
        "candidates": [{
            "content": {"parts": [{"functionCall": {"name": "search", "args": {"q": "AI"}}}]},
            "finishReason": "STOP"
        }]
    }
    res = client._parse_gemini_response(mock_api_res)
    assert res["tool_calls"][0]["name"] == "search"
    assert res["tool_calls"][0]["arguments"]["q"] == "AI"

# --- Generation Tests (Mocking HTTPX) ---
@pytest.mark.asyncio
async def test_generate_text_success(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "Generated"}]}}]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        res = await client.generate_text("Hi")
        assert res["text"] == "Generated"
        
        # Verify inputs
        call_kwargs = mock_post.call_args.kwargs
        payload = call_kwargs["json"]
        assert payload["generationConfig"]["temperature"] == 0.5

@pytest.mark.asyncio
async def test_generate_text_with_tools_and_system(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        await client.generate_text(
            "Hi", 
            system_instruction="Be polite",
            tools=[{"name": "tool1", "parameters": {}}]
        )
        
        payload = mock_post.call_args.kwargs["json"]
        assert "tools" in payload
        # System instruction should contain temporal context logic
        assert "Be polite" in payload["systemInstruction"]["parts"][0]["text"]

@pytest.mark.asyncio
async def test_generate_text_api_error(client):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        with pytest.raises(GeminiError) as exc:
            await client.generate_text("Hi")
        assert "500" in str(exc.value)

# --- Embedding Tests ---
@pytest.mark.asyncio
async def test_generate_embeddings_success(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "embedding": {"values": [0.1, 0.2, 0.3]}
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        vec = await client.generate_embeddings("Text")
        assert vec == [0.1, 0.2, 0.3]

@pytest.mark.asyncio
async def test_generate_embeddings_error(client):
    mock_response = MagicMock()
    mock_response.status_code = 403

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        with pytest.raises(GeminiError):
            await client.generate_embeddings("Text")
