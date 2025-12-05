"""
Unit tests for Service Proxy.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, Request
from backend.services.api_gateway.core.proxy import ServiceProxy

@pytest.mark.asyncio
async def test_forward_request_success():
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        mock_request.return_value = mock_response
        
        proxy = ServiceProxy()
        
        # Mock request
        request = MagicMock(spec=Request)
        request.method = "GET"
        request.headers = {}
        request.query_params = {}
        request.body = AsyncMock(return_value=b"")
        
        response = await proxy.forward_request("meta_orchestrator", "health", request)
        
        assert response == {"status": "ok"}
        mock_request.assert_called_once()

@pytest.mark.asyncio
async def test_forward_request_service_not_found():
    proxy = ServiceProxy()
    request = MagicMock(spec=Request)
    
    with pytest.raises(HTTPException) as exc:
        await proxy.forward_request("unknown_service", "health", request)
    
    assert exc.value.status_code == 404

@pytest.mark.asyncio
async def test_shutdown():
    with patch("httpx.AsyncClient.aclose", new_callable=AsyncMock) as mock_close:
        proxy = ServiceProxy()
        await proxy.shutdown()
        mock_close.assert_called_once()
